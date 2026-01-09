"""
Embedding Indexer

Background indexer for populating ContentEmbedding records.
Extracts content from all modules and generates embeddings.
"""

import logging
from typing import List, Optional, Dict, Any, Generator, Tuple
from datetime import date

from django.db import transaction
from django.utils import timezone

from ..models import (
    ContentEmbedding,
    TipoConteudo,
    Sensibilidade,
    CONTENT_SENSITIVITY_MAP,
    CONTENT_TYPE_MAP
)
from .service import EmbeddingService, get_embedding_service

logger = logging.getLogger(__name__)


class ContentExtractor:
    """
    Extracts searchable content from database models.

    Each module (Finance, Security, Library, Planning) has specific
    extraction logic to generate optimized text for embedding.
    """

    @staticmethod
    def extract_expense(expense) -> Dict[str, Any]:
        """Extract content from an Expense record."""
        text_parts = [
            f"Despesa: {expense.description}",
            f"Valor: R$ {expense.value:.2f}",
            f"Data: {expense.date.strftime('%d/%m/%Y')}",
        ]
        if expense.category:
            text_parts.append(f"Categoria: {expense.category}")
        if expense.payment_method:
            text_parts.append(f"Pagamento: {expense.payment_method}")
        if hasattr(expense, 'notes') and expense.notes:
            text_parts.append(f"Notas: {expense.notes}")

        return {
            'texto_original': ' | '.join(text_parts),
            'texto_busca': ' '.join(text_parts),
            'data_referencia': expense.date,
            'tags': [expense.category] if expense.category else [],
            'metadata': {
                'value': float(expense.value),
                'category': expense.category,
                'payment_method': getattr(expense, 'payment_method', None),
            }
        }

    @staticmethod
    def extract_revenue(revenue) -> Dict[str, Any]:
        """Extract content from a Revenue record."""
        text_parts = [
            f"Receita: {revenue.description}",
            f"Valor: R$ {revenue.value:.2f}",
            f"Data: {revenue.date.strftime('%d/%m/%Y')}",
        ]
        if revenue.category:
            text_parts.append(f"Categoria: {revenue.category}")
        if hasattr(revenue, 'source') and revenue.source:
            text_parts.append(f"Fonte: {revenue.source}")

        return {
            'texto_original': ' | '.join(text_parts),
            'texto_busca': ' '.join(text_parts),
            'data_referencia': revenue.date,
            'tags': [revenue.category] if revenue.category else [],
            'metadata': {
                'value': float(revenue.value),
                'category': revenue.category,
            }
        }

    @staticmethod
    def extract_account(account) -> Dict[str, Any]:
        """Extract content from an Account record."""
        text_parts = [
            f"Conta: {account.name}",
            f"Tipo: {account.account_type}",
        ]
        if account.institution:
            text_parts.append(f"Instituicao: {account.institution}")
        if account.balance is not None:
            text_parts.append(f"Saldo: R$ {account.balance:.2f}")
        if hasattr(account, 'description') and account.description:
            text_parts.append(f"Descricao: {account.description}")

        return {
            'texto_original': ' | '.join(text_parts),
            'texto_busca': ' '.join(text_parts),
            'data_referencia': None,
            'tags': [account.account_type] if account.account_type else [],
            'metadata': {
                'account_type': account.account_type,
                'institution': account.institution,
                'balance': float(account.balance) if account.balance else None,
            }
        }

    @staticmethod
    def extract_credit_card(card) -> Dict[str, Any]:
        """Extract content from a CreditCard record."""
        text_parts = [
            f"Cartao de Credito: {card.name}",
        ]
        if hasattr(card, 'flag') and card.flag:
            text_parts.append(f"Bandeira: {card.flag}")
        if hasattr(card, 'credit_limit') and card.credit_limit:
            text_parts.append(f"Limite: R$ {card.credit_limit:.2f}")

        return {
            'texto_original': ' | '.join(text_parts),
            'texto_busca': ' '.join(text_parts),
            'data_referencia': None,
            'tags': [card.flag] if hasattr(card, 'flag') and card.flag else [],
            'metadata': {
                'flag': getattr(card, 'flag', None),
                'credit_limit': float(card.credit_limit) if hasattr(card, 'credit_limit') and card.credit_limit else None,
            }
        }

    @staticmethod
    def extract_book(book) -> Dict[str, Any]:
        """Extract content from a Book record."""
        text_parts = [
            f"Livro: {book.title}",
        ]

        # Handle authors (ManyToMany)
        if hasattr(book, 'authors') and book.authors.exists():
            authors = ', '.join([a.name for a in book.authors.all()])
            text_parts.append(f"Autor(es): {authors}")

        if hasattr(book, 'genre') and book.genre:
            text_parts.append(f"Genero: {book.genre}")
        if hasattr(book, 'pages') and book.pages:
            text_parts.append(f"Paginas: {book.pages}")
        if hasattr(book, 'synopsis') and book.synopsis:
            text_parts.append(f"Sinopse: {book.synopsis[:200]}")

        tags = []
        if hasattr(book, 'genre') and book.genre:
            tags.append(book.genre)
        if hasattr(book, 'literary_type') and book.literary_type:
            tags.append(book.literary_type)

        return {
            'texto_original': ' | '.join(text_parts),
            'texto_busca': ' '.join(text_parts),
            'data_referencia': None,
            'tags': tags,
            'metadata': {
                'genre': getattr(book, 'genre', None),
                'pages': getattr(book, 'pages', None),
                'rating': getattr(book, 'rating', None),
            }
        }

    @staticmethod
    def extract_password(password) -> Dict[str, Any]:
        """
        Extract content from a Password record.

        NOTE: The actual password is NEVER included in the embedding.
        Only metadata like name, website, and username are indexed.
        """
        text_parts = [
            f"Senha: {password.name}",
        ]
        if hasattr(password, 'website') and password.website:
            text_parts.append(f"Site: {password.website}")
        if hasattr(password, 'username') and password.username:
            text_parts.append(f"Usuario: {password.username}")

        return {
            'texto_original': ' | '.join(text_parts),
            'texto_busca': ' '.join(text_parts),
            'data_referencia': None,
            'tags': ['senha', 'credencial'],
            'metadata': {
                'website': getattr(password, 'website', None),
                'has_username': bool(getattr(password, 'username', None)),
            }
        }

    @staticmethod
    def extract_goal(goal) -> Dict[str, Any]:
        """Extract content from a Goal record."""
        text_parts = [
            f"Meta: {goal.name}",
        ]
        if hasattr(goal, 'description') and goal.description:
            text_parts.append(f"Descricao: {goal.description}")
        if hasattr(goal, 'goal_type') and goal.goal_type:
            text_parts.append(f"Tipo: {goal.goal_type}")
        if hasattr(goal, 'status') and goal.status:
            text_parts.append(f"Status: {goal.status}")

        return {
            'texto_original': ' | '.join(text_parts),
            'texto_busca': ' '.join(text_parts),
            'data_referencia': getattr(goal, 'start_date', None),
            'tags': [goal.goal_type] if hasattr(goal, 'goal_type') and goal.goal_type else [],
            'metadata': {
                'goal_type': getattr(goal, 'goal_type', None),
                'status': getattr(goal, 'status', None),
            }
        }

    @staticmethod
    def extract_routine_task(task) -> Dict[str, Any]:
        """Extract content from a RoutineTask record."""
        text_parts = [
            f"Tarefa: {task.name}",
        ]
        if hasattr(task, 'description') and task.description:
            text_parts.append(f"Descricao: {task.description}")
        if hasattr(task, 'category') and task.category:
            text_parts.append(f"Categoria: {task.category}")
        if hasattr(task, 'periodicity') and task.periodicity:
            text_parts.append(f"Periodicidade: {task.periodicity}")

        return {
            'texto_original': ' | '.join(text_parts),
            'texto_busca': ' '.join(text_parts),
            'data_referencia': None,
            'tags': [task.category] if hasattr(task, 'category') and task.category else [],
            'metadata': {
                'category': getattr(task, 'category', None),
                'periodicity': getattr(task, 'periodicity', None),
                'is_active': getattr(task, 'is_active', True),
            }
        }

    @staticmethod
    def extract_daily_reflection(reflection) -> Dict[str, Any]:
        """Extract content from a DailyReflection record."""
        text_parts = [
            f"Reflexao do dia {reflection.date.strftime('%d/%m/%Y')}",
        ]
        if hasattr(reflection, 'mood') and reflection.mood:
            text_parts.append(f"Humor: {reflection.mood}")
        if hasattr(reflection, 'notes') and reflection.notes:
            # Truncate long notes
            notes = reflection.notes[:500] if len(reflection.notes) > 500 else reflection.notes
            text_parts.append(f"Notas: {notes}")

        return {
            'texto_original': ' | '.join(text_parts),
            'texto_busca': ' '.join(text_parts),
            'data_referencia': reflection.date,
            'tags': [reflection.mood] if hasattr(reflection, 'mood') and reflection.mood else [],
            'metadata': {
                'mood': getattr(reflection, 'mood', None),
            }
        }


class EmbeddingIndexer:
    """
    Indexes content from all modules into ContentEmbedding records.

    This class handles the extraction of content from various models,
    generation of embeddings, and storage in the database.
    """

    # Model configuration: (model_class_path, content_type, extractor_method)
    MODEL_CONFIG = [
        ('expenses.models.Expense', 'expense', 'extract_expense'),
        ('revenues.models.Revenue', 'revenue', 'extract_revenue'),
        ('accounts.models.Account', 'account', 'extract_account'),
        ('credit_cards.models.CreditCard', 'creditcard', 'extract_credit_card'),
        ('library.models.Book', 'book', 'extract_book'),
        ('security.models.Password', 'password', 'extract_password'),
        ('personal_planning.models.Goal', 'goal', 'extract_goal'),
        ('personal_planning.models.RoutineTask', 'routinetask', 'extract_routine_task'),
        ('personal_planning.models.DailyReflection', 'dailyreflection', 'extract_daily_reflection'),
    ]

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        batch_size: int = 50
    ):
        self.embedding_service = embedding_service or get_embedding_service()
        self.batch_size = batch_size
        self.extractor = ContentExtractor()

    def _get_model_class(self, model_path: str):
        """Dynamically import a model class from its path."""
        from django.apps import apps
        parts = model_path.rsplit('.', 2)
        app_label = parts[0]
        model_name = parts[-1]
        try:
            return apps.get_model(app_label, model_name)
        except LookupError:
            logger.warning(f"Model not found: {model_path}")
            return None

    def _get_owner(self, instance) -> Optional[Any]:
        """Get the owner (Member) from a model instance."""
        if hasattr(instance, 'owner'):
            return instance.owner
        if hasattr(instance, 'member'):
            return instance.member
        return None

    def index_single(
        self,
        content_type: str,
        content_id: int,
        owner_id: int,
        force: bool = False
    ) -> Optional[ContentEmbedding]:
        """
        Index a single content item.

        Parameters
        ----------
        content_type : str
            The type of content (e.g., 'expense', 'book')
        content_id : int
            The ID of the content
        owner_id : int
            The owner's ID
        force : bool
            If True, re-index even if already indexed

        Returns
        -------
        ContentEmbedding or None
            The created/updated embedding record
        """
        from members.models import Member

        # Find the model config
        model_config = None
        for path, ctype, extractor_name in self.MODEL_CONFIG:
            if ctype == content_type:
                model_config = (path, ctype, extractor_name)
                break

        if not model_config:
            logger.warning(f"Unknown content type: {content_type}")
            return None

        model_path, ctype, extractor_name = model_config
        Model = self._get_model_class(model_path)
        if Model is None:
            return None

        try:
            owner = Member.objects.get(id=owner_id)
            instance = Model.objects.get(id=content_id)
        except (Member.DoesNotExist, Model.DoesNotExist):
            logger.warning(f"Content not found: {content_type}:{content_id}")
            return None

        # Check if already indexed
        existing = ContentEmbedding.objects.filter(
            content_type=ctype,
            content_id=content_id,
            owner=owner
        ).first()

        if existing and existing.is_indexed and not force:
            logger.debug(f"Already indexed: {content_type}:{content_id}")
            return existing

        # Extract content
        extractor_method = getattr(self.extractor, extractor_name)
        content_data = extractor_method(instance)

        # Generate embedding
        try:
            embedding_result = self.embedding_service.generate(content_data['texto_busca'])
        except Exception as e:
            logger.error(f"Failed to generate embedding for {content_type}:{content_id}: {e}")
            return None

        # Create or update ContentEmbedding
        tipo = CONTENT_TYPE_MAP.get(ctype, TipoConteudo.FINANCEIRO)
        sensibilidade = CONTENT_SENSITIVITY_MAP.get(ctype, Sensibilidade.BAIXA)

        embedding_record, created = ContentEmbedding.objects.update_or_create(
            content_type=ctype,
            content_id=content_id,
            owner=owner,
            defaults={
                'tipo': tipo,
                'sensibilidade': sensibilidade,
                'tags': content_data.get('tags', []),
                'data_referencia': content_data.get('data_referencia'),
                'texto_original': content_data['texto_original'],
                'texto_busca': content_data['texto_busca'],
                'embedding': embedding_result.embedding,
                'metadata': content_data.get('metadata', {}),
                'is_indexed': True,
                'indexed_at': timezone.now(),
                'embedding_model': embedding_result.model,
            }
        )

        action = "Created" if created else "Updated"
        logger.info(f"{action} embedding for {content_type}:{content_id}")

        return embedding_record

    def index_module(
        self,
        module: str,
        owner_id: Optional[int] = None,
        batch_size: Optional[int] = None
    ) -> Tuple[int, int]:
        """
        Index all content from a specific module.

        Parameters
        ----------
        module : str
            Module name ('finance', 'security', 'library', 'planning')
        owner_id : int, optional
            If provided, only index for this owner
        batch_size : int, optional
            Batch size for processing

        Returns
        -------
        Tuple[int, int]
            (indexed_count, error_count)
        """
        batch_size = batch_size or self.batch_size

        # Map module to content types
        module_types = {
            'finance': ['expense', 'revenue', 'account', 'creditcard'],
            'security': ['password'],
            'library': ['book'],
            'planning': ['goal', 'routinetask', 'dailyreflection'],
        }

        content_types = module_types.get(module, [])
        if not content_types:
            logger.warning(f"Unknown module: {module}")
            return (0, 0)

        indexed = 0
        errors = 0

        for content_type in content_types:
            # Find model config
            for path, ctype, extractor_name in self.MODEL_CONFIG:
                if ctype == content_type:
                    Model = self._get_model_class(path)
                    if Model is None:
                        continue

                    queryset = Model.objects.filter(deleted_at__isnull=True)
                    if owner_id:
                        if hasattr(Model, 'owner'):
                            queryset = queryset.filter(owner_id=owner_id)
                        elif hasattr(Model, 'member'):
                            queryset = queryset.filter(member_id=owner_id)

                    for instance in queryset.iterator(chunk_size=batch_size):
                        owner = self._get_owner(instance)
                        if owner:
                            try:
                                self.index_single(ctype, instance.id, owner.id)
                                indexed += 1
                            except Exception as e:
                                logger.error(f"Error indexing {ctype}:{instance.id}: {e}")
                                errors += 1

        return (indexed, errors)

    def index_all(
        self,
        owner_id: Optional[int] = None,
        batch_size: Optional[int] = None
    ) -> Tuple[int, int]:
        """
        Index all content from all modules.

        Parameters
        ----------
        owner_id : int, optional
            If provided, only index for this owner
        batch_size : int, optional
            Batch size for processing

        Returns
        -------
        Tuple[int, int]
            (indexed_count, error_count)
        """
        total_indexed = 0
        total_errors = 0

        for module in ['finance', 'security', 'library', 'planning']:
            indexed, errors = self.index_module(module, owner_id, batch_size)
            total_indexed += indexed
            total_errors += errors
            logger.info(f"Module {module}: indexed={indexed}, errors={errors}")

        logger.info(f"Total: indexed={total_indexed}, errors={total_errors}")
        return (total_indexed, total_errors)

    def clear_embeddings(
        self,
        owner_id: Optional[int] = None,
        content_type: Optional[str] = None
    ) -> int:
        """
        Clear embeddings from the database.

        Parameters
        ----------
        owner_id : int, optional
            If provided, only clear for this owner
        content_type : str, optional
            If provided, only clear this content type

        Returns
        -------
        int
            Number of records deleted
        """
        queryset = ContentEmbedding.objects.all()

        if owner_id:
            queryset = queryset.filter(owner_id=owner_id)
        if content_type:
            queryset = queryset.filter(content_type=content_type)

        count, _ = queryset.delete()
        logger.info(f"Cleared {count} embedding records")
        return count
