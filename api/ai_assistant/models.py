"""
AI Assistant Models

This module contains the database models for the AI Assistant RAG system,
including the ContentEmbedding model for storing vector embeddings with
pgvector support.
"""

from django.db import models
from django.contrib.postgres.fields import ArrayField
from pgvector.django import VectorField

from app.models import BaseModel


class TipoConteudo(models.TextChoices):
    """Content type classification for RAG retrieval."""
    PLANEJAMENTO = 'planejamento', 'Planejamento Pessoal'
    SEGURANCA = 'seguranca', 'Seguranca'
    FINANCEIRO = 'financeiro', 'Financeiro'
    LEITURA = 'leitura', 'Leitura/Biblioteca'


class Sensibilidade(models.TextChoices):
    """
    Sensitivity classification for LLM routing.

    ALTA: Data must NEVER leave local infrastructure (Ollama only)
    MEDIA: Prefer local, but can use cloud for complex queries
    BAIXA: Can be processed by any LLM provider
    """
    BAIXA = 'baixa', 'Baixa'
    MEDIA = 'media', 'Media'
    ALTA = 'alta', 'Alta'


class ContentEmbedding(BaseModel):
    """
    Stores embeddings for all searchable content across modules.

    This model uses pgvector for efficient similarity search and supports
    filtering by content type, sensitivity level, tags, and date range.

    The embedding is generated using nomic-embed-text (768 dimensions) via
    Ollama local inference to ensure sensitive data never leaves the
    infrastructure.

    Attributes
    ----------
    content_type : str
        The entity type (e.g., 'expense', 'book', 'password', 'goal')
    content_id : int
        The primary key of the source entity
    tipo : TipoConteudo
        Classification for module filtering (planejamento, seguranca, etc.)
    sensibilidade : Sensibilidade
        Sensitivity level for LLM routing decisions
    tags : list[str]
        Searchable tags for additional filtering
    data_referencia : date
        Reference date for temporal filtering (expense date, reading date, etc.)
    texto_original : str
        Human-readable text for display in search results
    texto_busca : str
        Optimized text used for embedding generation
    embedding : Vector
        768-dimensional vector from nomic-embed-text model
    metadata : dict
        Additional entity-specific metadata (JSON)
    owner : Member
        The user who owns this content
    is_indexed : bool
        Whether the embedding has been generated
    indexed_at : datetime
        When the embedding was generated
    embedding_model : str
        The model used for embedding generation
    """

    # Content identification
    content_type = models.CharField(
        max_length=100,
        verbose_name='Tipo de Entidade',
        help_text='Entity type: expense, book, password, goal, etc.',
        db_index=True
    )
    content_id = models.PositiveIntegerField(
        verbose_name='ID da Entidade'
    )

    # Classification for filtering and routing
    tipo = models.CharField(
        max_length=20,
        choices=TipoConteudo.choices,
        verbose_name='Tipo',
        db_index=True
    )
    sensibilidade = models.CharField(
        max_length=10,
        choices=Sensibilidade.choices,
        default=Sensibilidade.BAIXA,
        verbose_name='Sensibilidade',
        db_index=True
    )
    tags = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
        verbose_name='Tags',
        help_text='Searchable tags for filtering'
    )

    # Temporal reference for date-based filtering
    data_referencia = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Referencia',
        help_text='Reference date (expense date, reading date, etc.)',
        db_index=True
    )

    # Content
    texto_original = models.TextField(
        verbose_name='Texto Original',
        help_text='Human-readable text for display'
    )
    texto_busca = models.TextField(
        verbose_name='Texto para Busca',
        help_text='Optimized text for embedding generation'
    )

    # Embedding vector (768 dimensions for nomic-embed-text)
    embedding = VectorField(
        dimensions=768,
        null=True,
        blank=True,
        verbose_name='Vetor de Embedding'
    )

    # Additional metadata (JSON)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Metadados Adicionais',
        help_text='Entity-specific metadata for rich search results'
    )

    # Ownership - Links to the user who owns this content
    owner = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='content_embeddings',
        verbose_name='Proprietario'
    )

    # Indexing status
    is_indexed = models.BooleanField(
        default=False,
        verbose_name='Indexado',
        db_index=True
    )
    indexed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data de Indexacao'
    )
    embedding_model = models.CharField(
        max_length=100,
        default='nomic-embed-text',
        verbose_name='Modelo de Embedding'
    )

    class Meta:
        verbose_name = 'Embedding de Conteudo'
        verbose_name_plural = 'Embeddings de Conteudo'
        ordering = ['-created_at']
        # Ensure uniqueness per content per owner
        unique_together = [['content_type', 'content_id', 'owner']]
        indexes = [
            # Composite indexes for common query patterns
            models.Index(fields=['owner', 'tipo'], name='idx_owner_tipo'),
            models.Index(fields=['owner', 'sensibilidade'], name='idx_owner_sens'),
            models.Index(fields=['owner', 'is_indexed'], name='idx_owner_indexed'),
            models.Index(fields=['content_type', 'content_id'], name='idx_content_ref'),
            models.Index(fields=['owner', '-data_referencia'], name='idx_owner_data'),
        ]

    def __str__(self):
        return f"{self.content_type}:{self.content_id} ({self.tipo}/{self.sensibilidade})"

    def mark_indexed(self):
        """Mark this content as indexed with current timestamp."""
        from django.utils import timezone
        self.is_indexed = True
        self.indexed_at = timezone.now()
        self.save(update_fields=['is_indexed', 'indexed_at', 'updated_at'])

    def clear_embedding(self):
        """Clear embedding data (for re-indexing)."""
        self.embedding = None
        self.is_indexed = False
        self.indexed_at = None
        self.save(update_fields=['embedding', 'is_indexed', 'indexed_at', 'updated_at'])


# Mapping of content types to their sensitivity levels
# Used by the indexer to automatically classify content
CONTENT_SENSITIVITY_MAP = {
    # Security module - ALWAYS HIGH sensitivity
    'password': Sensibilidade.ALTA,
    'storedcreditcard': Sensibilidade.ALTA,
    'storedbankaccount': Sensibilidade.ALTA,
    'archive': Sensibilidade.MEDIA,  # Depends on content, default to MEDIA

    # Finance module
    'account': Sensibilidade.MEDIA,  # Balance info
    'creditcard': Sensibilidade.MEDIA,  # Credit limits
    'expense': Sensibilidade.BAIXA,  # Transaction history
    'revenue': Sensibilidade.BAIXA,  # Income history
    'transfer': Sensibilidade.BAIXA,  # Movement records
    'loan': Sensibilidade.MEDIA,  # Debt information
    'creditcardexpense': Sensibilidade.BAIXA,

    # Library module
    'book': Sensibilidade.BAIXA,
    'summary': Sensibilidade.BAIXA,
    'reading': Sensibilidade.BAIXA,

    # Personal Planning module
    'routinetask': Sensibilidade.BAIXA,
    'dailytaskrecord': Sensibilidade.BAIXA,
    'goal': Sensibilidade.BAIXA,
    'dailyreflection': Sensibilidade.MEDIA,  # Personal thoughts
}

# Mapping of content types to their module (tipo)
CONTENT_TYPE_MAP = {
    # Security
    'password': TipoConteudo.SEGURANCA,
    'storedcreditcard': TipoConteudo.SEGURANCA,
    'storedbankaccount': TipoConteudo.SEGURANCA,
    'archive': TipoConteudo.SEGURANCA,

    # Finance
    'account': TipoConteudo.FINANCEIRO,
    'creditcard': TipoConteudo.FINANCEIRO,
    'expense': TipoConteudo.FINANCEIRO,
    'revenue': TipoConteudo.FINANCEIRO,
    'transfer': TipoConteudo.FINANCEIRO,
    'loan': TipoConteudo.FINANCEIRO,
    'creditcardexpense': TipoConteudo.FINANCEIRO,

    # Library
    'book': TipoConteudo.LEITURA,
    'summary': TipoConteudo.LEITURA,
    'reading': TipoConteudo.LEITURA,

    # Personal Planning
    'routinetask': TipoConteudo.PLANEJAMENTO,
    'dailytaskrecord': TipoConteudo.PLANEJAMENTO,
    'goal': TipoConteudo.PLANEJAMENTO,
    'dailyreflection': TipoConteudo.PLANEJAMENTO,
}
