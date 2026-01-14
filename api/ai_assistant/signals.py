"""
AI Assistant Signals

Automatically updates RAG embeddings when content is created, updated, or deleted.
This ensures the AI assistant always has access to the most up-to-date information.
"""

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings

logger = logging.getLogger(__name__)


def get_owner_id(instance):
    """
    Get the owner ID from a model instance.
    Handles different field names (owner, member) across models.
    """
    if hasattr(instance, 'owner') and instance.owner:
        return instance.owner.id
    if hasattr(instance, 'member') and instance.member:
        return instance.member.id
    return None


def index_content_async(content_type: str, content_id: int, owner_id: int):
    """
    Index content embedding.
    In production, this could be made async using Celery or similar.
    """
    try:
        from .embeddings.indexer import EmbeddingIndexer
        indexer = EmbeddingIndexer()
        indexer.index_single(content_type, content_id, owner_id, force=True)
        logger.info(f"Indexed {content_type}:{content_id} for owner {owner_id}")
    except Exception as e:
        logger.error(f"Failed to index {content_type}:{content_id}: {e}")


def delete_embedding(content_type: str, content_id: int, owner_id: int):
    """
    Delete embedding when content is deleted.
    """
    try:
        from .models import ContentEmbedding
        deleted, _ = ContentEmbedding.objects.filter(
            content_type=content_type,
            content_id=content_id,
            owner_id=owner_id
        ).delete()
        if deleted:
            logger.info(f"Deleted embedding for {content_type}:{content_id}")
    except Exception as e:
        logger.error(f"Failed to delete embedding for {content_type}:{content_id}: {e}")


# =============================================================================
# FINANCE MODULE SIGNALS
# =============================================================================

@receiver(post_save, sender='expenses.Expense')
def update_expense_embedding(sender, instance, created, **kwargs):
    """Update embedding when expense is created or updated."""
    owner_id = get_owner_id(instance)
    if owner_id:
        index_content_async('expense', instance.id, owner_id)


@receiver(post_delete, sender='expenses.Expense')
def delete_expense_embedding(sender, instance, **kwargs):
    """Delete embedding when expense is deleted."""
    owner_id = get_owner_id(instance)
    if owner_id:
        delete_embedding('expense', instance.id, owner_id)


@receiver(post_save, sender='revenues.Revenue')
def update_revenue_embedding(sender, instance, created, **kwargs):
    """Update embedding when revenue is created or updated."""
    owner_id = get_owner_id(instance)
    if owner_id:
        index_content_async('revenue', instance.id, owner_id)


@receiver(post_delete, sender='revenues.Revenue')
def delete_revenue_embedding(sender, instance, **kwargs):
    """Delete embedding when revenue is deleted."""
    owner_id = get_owner_id(instance)
    if owner_id:
        delete_embedding('revenue', instance.id, owner_id)


@receiver(post_save, sender='accounts.Account')
def update_account_embedding(sender, instance, created, **kwargs):
    """Update embedding when account is created or updated."""
    owner_id = get_owner_id(instance)
    if owner_id:
        index_content_async('account', instance.id, owner_id)


@receiver(post_delete, sender='accounts.Account')
def delete_account_embedding(sender, instance, **kwargs):
    """Delete embedding when account is deleted."""
    owner_id = get_owner_id(instance)
    if owner_id:
        delete_embedding('account', instance.id, owner_id)


@receiver(post_save, sender='credit_cards.CreditCard')
def update_credit_card_embedding(sender, instance, created, **kwargs):
    """Update embedding when credit card is created or updated."""
    owner_id = get_owner_id(instance)
    if owner_id:
        index_content_async('creditcard', instance.id, owner_id)


@receiver(post_delete, sender='credit_cards.CreditCard')
def delete_credit_card_embedding(sender, instance, **kwargs):
    """Delete embedding when credit card is deleted."""
    owner_id = get_owner_id(instance)
    if owner_id:
        delete_embedding('creditcard', instance.id, owner_id)


# =============================================================================
# SECURITY MODULE SIGNALS
# =============================================================================

@receiver(post_save, sender='security.Password')
def update_password_embedding(sender, instance, created, **kwargs):
    """Update embedding when password is created or updated."""
    owner_id = get_owner_id(instance)
    if owner_id:
        index_content_async('password', instance.id, owner_id)


@receiver(post_delete, sender='security.Password')
def delete_password_embedding(sender, instance, **kwargs):
    """Delete embedding when password is deleted."""
    owner_id = get_owner_id(instance)
    if owner_id:
        delete_embedding('password', instance.id, owner_id)


# =============================================================================
# LIBRARY MODULE SIGNALS
# =============================================================================

@receiver(post_save, sender='library.Book')
def update_book_embedding(sender, instance, created, **kwargs):
    """Update embedding when book is created or updated."""
    owner_id = get_owner_id(instance)
    if owner_id:
        index_content_async('book', instance.id, owner_id)


@receiver(post_delete, sender='library.Book')
def delete_book_embedding(sender, instance, **kwargs):
    """Delete embedding when book is deleted."""
    owner_id = get_owner_id(instance)
    if owner_id:
        delete_embedding('book', instance.id, owner_id)


# =============================================================================
# PERSONAL PLANNING MODULE SIGNALS
# =============================================================================

@receiver(post_save, sender='personal_planning.Goal')
def update_goal_embedding(sender, instance, created, **kwargs):
    """Update embedding when goal is created or updated."""
    owner_id = get_owner_id(instance)
    if owner_id:
        index_content_async('goal', instance.id, owner_id)


@receiver(post_delete, sender='personal_planning.Goal')
def delete_goal_embedding(sender, instance, **kwargs):
    """Delete embedding when goal is deleted."""
    owner_id = get_owner_id(instance)
    if owner_id:
        delete_embedding('goal', instance.id, owner_id)


@receiver(post_save, sender='personal_planning.RoutineTask')
def update_routine_task_embedding(sender, instance, created, **kwargs):
    """Update embedding when routine task is created or updated."""
    owner_id = get_owner_id(instance)
    if owner_id:
        index_content_async('routinetask', instance.id, owner_id)


@receiver(post_delete, sender='personal_planning.RoutineTask')
def delete_routine_task_embedding(sender, instance, **kwargs):
    """Delete embedding when routine task is deleted."""
    owner_id = get_owner_id(instance)
    if owner_id:
        delete_embedding('routinetask', instance.id, owner_id)


@receiver(post_save, sender='personal_planning.DailyReflection')
def update_daily_reflection_embedding(sender, instance, created, **kwargs):
    """Update embedding when daily reflection is created or updated."""
    owner_id = get_owner_id(instance)
    if owner_id:
        index_content_async('dailyreflection', instance.id, owner_id)


@receiver(post_delete, sender='personal_planning.DailyReflection')
def delete_daily_reflection_embedding(sender, instance, **kwargs):
    """Delete embedding when daily reflection is deleted."""
    owner_id = get_owner_id(instance)
    if owner_id:
        delete_embedding('dailyreflection', instance.id, owner_id)
