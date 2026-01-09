"""
Management command to populate embeddings for existing content.

Usage:
    python manage.py populate_embeddings --module=all
    python manage.py populate_embeddings --module=finance --batch-size=100
    python manage.py populate_embeddings --clear --module=all
"""

import time
from django.core.management.base import BaseCommand, CommandError

from ai_assistant.embeddings.indexer import EmbeddingIndexer
from ai_assistant.embeddings.service import get_embedding_service


class Command(BaseCommand):
    help = 'Populate embeddings for existing content in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--module',
            type=str,
            choices=['finance', 'security', 'library', 'planning', 'all'],
            default='all',
            help='Module to index (default: all)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Batch size for processing (default: 50)'
        )
        parser.add_argument(
            '--owner-id',
            type=int,
            default=None,
            help='Only index for a specific owner ID'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing embeddings before indexing'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be indexed without actually indexing'
        )

    def handle(self, *args, **options):
        module = options['module']
        batch_size = options['batch_size']
        owner_id = options['owner_id']
        clear = options['clear']
        dry_run = options['dry_run']

        self.stdout.write(self.style.NOTICE(
            f"\n{'='*60}\n"
            f"PersonalHub Embedding Population\n"
            f"{'='*60}\n"
        ))

        # Check Ollama availability
        self.stdout.write("Checking Ollama availability...")
        try:
            embedding_service = get_embedding_service()
            if not embedding_service.health_check():
                raise CommandError(
                    "Ollama is not available. Please ensure:\n"
                    "1. Ollama is running (docker-compose up -d ollama)\n"
                    "2. The model is installed (docker-compose exec ollama ollama pull nomic-embed-text)"
                )
            self.stdout.write(self.style.SUCCESS("Ollama is available"))
        except Exception as e:
            raise CommandError(f"Failed to connect to Ollama: {e}")

        indexer = EmbeddingIndexer(batch_size=batch_size)

        # Clear existing embeddings if requested
        if clear and not dry_run:
            self.stdout.write(self.style.WARNING("\nClearing existing embeddings..."))
            content_type = None
            if module != 'all':
                # Map module to content types
                module_types = {
                    'finance': ['expense', 'revenue', 'account', 'creditcard'],
                    'security': ['password'],
                    'library': ['book'],
                    'planning': ['goal', 'routinetask', 'dailyreflection'],
                }
                # Clear each content type
                for ct in module_types.get(module, []):
                    count = indexer.clear_embeddings(owner_id=owner_id, content_type=ct)
                    self.stdout.write(f"  Cleared {count} {ct} embeddings")
            else:
                count = indexer.clear_embeddings(owner_id=owner_id)
                self.stdout.write(f"  Cleared {count} total embeddings")

        if dry_run:
            self.stdout.write(self.style.WARNING("\n[DRY RUN] No changes will be made\n"))
            self._show_stats(indexer, module, owner_id)
            return

        # Index content
        self.stdout.write(self.style.NOTICE(f"\nIndexing module: {module}"))
        self.stdout.write(f"Batch size: {batch_size}")
        if owner_id:
            self.stdout.write(f"Owner ID: {owner_id}")

        start_time = time.time()

        if module == 'all':
            indexed, errors = indexer.index_all(owner_id=owner_id, batch_size=batch_size)
        else:
            indexed, errors = indexer.index_module(
                module=module,
                owner_id=owner_id,
                batch_size=batch_size
            )

        elapsed = time.time() - start_time

        # Summary
        self.stdout.write(self.style.SUCCESS(
            f"\n{'='*60}\n"
            f"Indexing Complete\n"
            f"{'='*60}\n"
            f"Indexed: {indexed}\n"
            f"Errors: {errors}\n"
            f"Time: {elapsed:.2f}s\n"
            f"Rate: {indexed/elapsed:.1f} items/second\n" if elapsed > 0 else ""
        ))

        if errors > 0:
            self.stdout.write(self.style.WARNING(
                f"\n{errors} items failed to index. Check logs for details."
            ))

    def _show_stats(self, indexer, module, owner_id):
        """Show stats for dry run."""
        from ai_assistant.models import ContentEmbedding
        from django.db.models import Count

        self.stdout.write("\nCurrent embedding statistics:")

        queryset = ContentEmbedding.objects.all()
        if owner_id:
            queryset = queryset.filter(owner_id=owner_id)

        # Count by tipo
        by_tipo = queryset.values('tipo').annotate(count=Count('id'))
        for item in by_tipo:
            self.stdout.write(f"  {item['tipo']}: {item['count']}")

        # Count indexed
        total = queryset.count()
        indexed = queryset.filter(is_indexed=True).count()
        self.stdout.write(f"\nTotal: {total}")
        self.stdout.write(f"Indexed: {indexed}")
        self.stdout.write(f"Pending: {total - indexed}")
