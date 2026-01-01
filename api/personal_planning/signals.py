"""
Signals para atualizacao automatica de progresso de objetivos.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


@receiver(post_save, sender='personal_planning.DailyTaskRecord')
def update_goal_progress_on_record_save(sender, instance, created, **kwargs):
    """
    Atualiza progresso de objetivo quando uma tarefa relacionada e cumprida.
    """
    from personal_planning.models import Goal

    if not instance.completed:
        return

    # Buscar objetivos ativos relacionados a esta tarefa
    goals = Goal.objects.filter(
        related_task=instance.task,
        status='active',
        deleted_at__isnull=True
    )

    for goal in goals:
        if goal.goal_type in ['consecutive_days', 'total_days']:
            # Incrementar progresso
            goal.current_value += 1

            # Verificar se objetivo foi cumprido
            if goal.current_value >= goal.target_value:
                goal.status = 'completed'
                goal.end_date = timezone.now().date()

            goal.save(update_fields=['current_value', 'status', 'end_date'])
