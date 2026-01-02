from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from app.models import BaseModel


# ============================================================================
# CHOICE CONSTANTS
# ============================================================================

TASK_CATEGORY_CHOICES = (
    ('health', 'Saúde'),
    ('studies', 'Estudos'),
    ('spiritual', 'Espiritual'),
    ('exercise', 'Exercício Físico'),
    ('nutrition', 'Nutrição'),
    ('meditation', 'Meditação'),
    ('reading', 'Leitura'),
    ('writing', 'Escrita'),
    ('work', 'Trabalho'),
    ('leisure', 'Lazer'),
    ('family', 'Família'),
    ('social', 'Social'),
    ('finance', 'Finanças'),
    ('household', 'Casa'),
    ('personal_care', 'Cuidado Pessoal'),
    ('other', 'Outros')
)

PERIODICITY_CHOICES = (
    ('daily', 'Diária'),
    ('weekdays', 'Dias Úteis'),
    ('weekly', 'Semanal'),
    ('monthly', 'Mensal'),
    ('custom', 'Personalizado')
)

# Dias da semana para tarefas semanais
WEEKDAY_CHOICES = (
    (0, 'Segunda-feira'),
    (1, 'Terça-feira'),
    (2, 'Quarta-feira'),
    (3, 'Quinta-feira'),
    (4, 'Sexta-feira'),
    (5, 'Sábado'),
    (6, 'Domingo')
)

GOAL_TYPE_CHOICES = (
    ('consecutive_days', 'Dias Consecutivos'),
    ('total_days', 'Total de Dias'),
    ('avoid_habit', 'Evitar Hábito'),
    ('custom', 'Personalizado')
)

GOAL_STATUS_CHOICES = (
    ('active', 'Ativo'),
    ('completed', 'Concluído'),
    ('failed', 'Falhou'),
    ('cancelled', 'Cancelado')
)

MOOD_CHOICES = (
    ('excellent', 'Excelente'),
    ('good', 'Bom'),
    ('neutral', 'Neutro'),
    ('bad', 'Ruim'),
    ('terrible', 'Péssimo')
)


# ============================================================================
# ROUTINE TASK MODEL
# ============================================================================

class RoutineTask(BaseModel):
    """
    Modelo para tarefas rotineiras que devem ser cumpridas periodicamente.

    Exemplos: Meditar, Ir a academia, Beber 8 copos de agua, Ler 30 minutos
    """
    name = models.CharField(
        max_length=200,
        null=False,
        blank=False,
        verbose_name='Nome da Tarefa'
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='Descricao'
    )
    category = models.CharField(
        max_length=50,
        choices=TASK_CATEGORY_CHOICES,
        null=False,
        blank=False,
        verbose_name='Categoria'
    )
    periodicity = models.CharField(
        max_length=20,
        choices=PERIODICITY_CHOICES,
        default='daily',
        verbose_name='Periodicidade'
    )
    # Para tarefas semanais: especificar dia da semana
    weekday = models.IntegerField(
        choices=WEEKDAY_CHOICES,
        null=True,
        blank=True,
        verbose_name='Dia da Semana',
        help_text='Apenas para tarefas semanais (0=Segunda, 6=Domingo)'
    )
    # Para tarefas mensais: especificar dia do mes
    day_of_month = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Dia do Mes',
        help_text='Apenas para tarefas mensais (1-31)'
    )
    # Para periodicidade personalizada
    custom_weekdays = models.JSONField(
        null=True,
        blank=True,
        default=None,
        verbose_name='Dias da Semana Personalizados',
        help_text='Array de dias da semana [0-6] para periodicidade personalizada'
    )
    custom_month_days = models.JSONField(
        null=True,
        blank=True,
        default=None,
        verbose_name='Dias do Mês Personalizados',
        help_text='Array de dias do mês [1-31] para periodicidade personalizada'
    )
    times_per_week = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Vezes por Semana',
        help_text='Quantas vezes por semana (para periodicidade personalizada)'
    )
    times_per_month = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Vezes por Mês',
        help_text='Quantas vezes por mês (para periodicidade personalizada)'
    )
    interval_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Intervalo em Dias',
        help_text='A cada X dias (para periodicidade personalizada)'
    )
    interval_start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Início do Intervalo',
        help_text='Data de referência para calcular intervalos'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Tarefa Ativa'
    )
    target_quantity = models.PositiveIntegerField(
        default=1,
        verbose_name='Quantidade Alvo',
        help_text='Ex: 8 copos de agua, 30 minutos de leitura'
    )
    unit = models.CharField(
        max_length=50,
        default='vez',
        verbose_name='Unidade',
        help_text='Ex: copos, minutos, paginas, vezes'
    )
    owner = models.ForeignKey(
        'members.Member',
        on_delete=models.PROTECT,
        related_name='routine_tasks',
        verbose_name='Proprietario'
    )

    class Meta:
        verbose_name = "Tarefa Rotineira"
        verbose_name_plural = "Tarefas Rotineiras"
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['owner', 'is_active']),
            models.Index(fields=['periodicity', 'is_active'])
        ]

    def clean(self):
        """Valida que campos de periodicidade estao corretos."""
        super().clean()

        if self.periodicity == 'weekly' and self.weekday is None:
            raise ValidationError({
                'weekday': 'Dia da semana e obrigatorio para tarefas semanais'
            })

        if self.periodicity == 'monthly':
            if self.day_of_month is None:
                raise ValidationError({
                    'day_of_month': 'Dia do mes e obrigatorio para tarefas mensais'
                })
            if self.day_of_month < 1 or self.day_of_month > 31:
                raise ValidationError({
                    'day_of_month': 'Dia do mes deve estar entre 1 e 31'
                })

        # Validação para periodicidade personalizada
        if self.periodicity == 'custom':
            has_weekdays = self.custom_weekdays and len(self.custom_weekdays) > 0
            has_month_days = self.custom_month_days and len(self.custom_month_days) > 0
            has_frequency = any([self.times_per_week, self.times_per_month, self.interval_days])

            if not (has_weekdays or has_month_days or has_frequency):
                raise ValidationError({
                    'periodicity': 'Periodicidade personalizada requer: dias da semana OU dias do mes OU frequencia'
                })

            # Validar valores dos dias da semana
            if self.custom_weekdays:
                if not all(isinstance(d, int) and 0 <= d <= 6 for d in self.custom_weekdays):
                    raise ValidationError({
                        'custom_weekdays': 'Dias da semana devem estar entre 0 (Segunda) e 6 (Domingo)'
                    })

            # Validar valores dos dias do mês
            if self.custom_month_days:
                if not all(isinstance(d, int) and 1 <= d <= 31 for d in self.custom_month_days):
                    raise ValidationError({
                        'custom_month_days': 'Dias do mes devem estar entre 1 e 31'
                    })

            # Validar intervalo de dias
            if self.interval_days and not self.interval_start_date:
                raise ValidationError({
                    'interval_start_date': 'Data de inicio e obrigatoria quando intervalo de dias esta definido'
                })

    def __str__(self):
        return f"{self.name} ({self.get_periodicity_display()})"

    def should_appear_on_date(self, date):
        """
        Verifica se esta tarefa deve aparecer em uma determinada data.

        Parameters
        ----------
        date : datetime.date
            Data a verificar

        Returns
        -------
        bool
            True se a tarefa deve aparecer nesta data
        """
        if not self.is_active:
            return False

        if self.periodicity == 'daily':
            return True

        # Dias úteis (Segunda a Sexta)
        if self.periodicity == 'weekdays':
            return date.weekday() in [0, 1, 2, 3, 4]

        if self.periodicity == 'weekly':
            return date.weekday() == self.weekday

        if self.periodicity == 'monthly':
            return date.day == self.day_of_month

        # Periodicidade personalizada
        if self.periodicity == 'custom':
            # Verificar dias da semana específicos
            if self.custom_weekdays:
                if date.weekday() not in self.custom_weekdays:
                    return False

            # Verificar dias do mês específicos
            if self.custom_month_days:
                if date.day not in self.custom_month_days:
                    return False

            # Verificar intervalo (a cada X dias)
            if self.interval_days and self.interval_start_date:
                delta = (date - self.interval_start_date).days
                if delta < 0 or delta % self.interval_days != 0:
                    return False

            # NOTA: times_per_week e times_per_month requerem lógica adicional
            # (verificar quantas vezes já foi marcada na semana/mês atual)
            # Por simplicidade, se apenas frequency estiver definida, sempre retorna True
            # A validação de frequência será feita no frontend/backend ao criar registros

            return True

        return False


# ============================================================================
# DAILY TASK RECORD MODEL
# ============================================================================

class DailyTaskRecord(BaseModel):
    """
    Registro de cumprimento (ou nao) de uma tarefa em um dia especifico.
    """
    task = models.ForeignKey(
        RoutineTask,
        on_delete=models.PROTECT,
        related_name='daily_records',
        verbose_name='Tarefa'
    )
    date = models.DateField(
        null=False,
        blank=False,
        verbose_name='Data'
    )
    completed = models.BooleanField(
        default=False,
        verbose_name='Cumprida'
    )
    quantity_completed = models.PositiveIntegerField(
        default=0,
        verbose_name='Quantidade Realizada',
        help_text='Quanto foi realizado (ex: 6 de 8 copos de agua)'
    )
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Observacoes'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Hora de Conclusao'
    )
    owner = models.ForeignKey(
        'members.Member',
        on_delete=models.PROTECT,
        related_name='daily_task_records',
        verbose_name='Proprietario'
    )

    class Meta:
        verbose_name = "Registro Diario de Tarefa"
        verbose_name_plural = "Registros Diarios de Tarefas"
        ordering = ['-date', 'task__category']
        unique_together = [['task', 'date', 'owner']]
        indexes = [
            models.Index(fields=['owner', '-date']),
            models.Index(fields=['task', '-date']),
            models.Index(fields=['completed', '-date'])
        ]

    def save(self, *args, **kwargs):
        """Atualiza completed_at quando tarefa e marcada como cumprida."""
        if self.completed and not self.completed_at:
            self.completed_at = timezone.now()
        elif not self.completed:
            self.completed_at = None
        super().save(*args, **kwargs)

    def __str__(self):
        status = "Cumprida" if self.completed else "Nao cumprida"
        return f"{self.task.name} - {self.date} ({status})"


# ============================================================================
# GOAL MODEL
# ============================================================================

class Goal(BaseModel):
    """
    Modelo para rastreamento de objetivos pessoais.

    Exemplos:
    - 15 dias sem alcool
    - 30 dias consecutivos de academia
    - Meditar 100 dias no total
    """
    title = models.CharField(
        max_length=200,
        null=False,
        blank=False,
        verbose_name='Titulo do Objetivo'
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='Descricao'
    )
    goal_type = models.CharField(
        max_length=30,
        choices=GOAL_TYPE_CHOICES,
        null=False,
        blank=False,
        verbose_name='Tipo de Objetivo'
    )
    related_task = models.ForeignKey(
        RoutineTask,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='goals',
        verbose_name='Tarefa Relacionada',
        help_text='Opcional: vincular objetivo a uma tarefa rotineira'
    )
    target_value = models.PositiveIntegerField(
        null=False,
        blank=False,
        verbose_name='Meta',
        help_text='Ex: 15 dias, 100 vezes, etc'
    )
    current_value = models.PositiveIntegerField(
        default=0,
        verbose_name='Valor Atual'
    )
    start_date = models.DateField(
        null=False,
        blank=False,
        default=timezone.now,
        verbose_name='Data de Inicio'
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Conclusao'
    )
    status = models.CharField(
        max_length=20,
        choices=GOAL_STATUS_CHOICES,
        default='active',
        verbose_name='Status'
    )
    owner = models.ForeignKey(
        'members.Member',
        on_delete=models.PROTECT,
        related_name='goals',
        verbose_name='Proprietario'
    )

    class Meta:
        verbose_name = "Objetivo"
        verbose_name_plural = "Objetivos"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['status', '-created_at'])
        ]

    @property
    def progress_percentage(self):
        """Calcula percentual de progresso do objetivo."""
        if self.target_value == 0:
            return 0.0
        return min((self.current_value / self.target_value) * 100, 100.0)

    @property
    def days_active(self):
        """Calcula quantos dias o objetivo esta ativo."""
        if self.end_date:
            return (self.end_date - self.start_date).days
        return (timezone.now().date() - self.start_date).days

    def __str__(self):
        return f"{self.title} ({self.current_value}/{self.target_value})"


# ============================================================================
# DAILY REFLECTION MODEL
# ============================================================================

class DailyReflection(BaseModel):
    """
    Modelo para anotacoes/reflexoes diarias (post-it do dia).
    """
    date = models.DateField(
        null=False,
        blank=False,
        verbose_name='Data'
    )
    reflection = models.TextField(
        null=False,
        blank=False,
        verbose_name='Reflexao do Dia'
    )
    mood = models.CharField(
        max_length=20,
        choices=MOOD_CHOICES,
        null=True,
        blank=True,
        verbose_name='Humor do Dia'
    )
    owner = models.ForeignKey(
        'members.Member',
        on_delete=models.PROTECT,
        related_name='daily_reflections',
        verbose_name='Proprietario'
    )

    class Meta:
        verbose_name = "Reflexao Diaria"
        verbose_name_plural = "Reflexoes Diarias"
        ordering = ['-date']
        unique_together = [['date', 'owner']]
        indexes = [
            models.Index(fields=['owner', '-date'])
        ]

    def __str__(self):
        return f"Reflexao de {self.date}"
