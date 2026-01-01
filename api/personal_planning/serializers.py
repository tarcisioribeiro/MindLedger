from rest_framework import serializers
from personal_planning.models import (
    RoutineTask, DailyTaskRecord, Goal, DailyReflection
)


# ============================================================================
# ROUTINE TASK SERIALIZERS
# ============================================================================

class RoutineTaskSerializer(serializers.ModelSerializer):
    """Serializer para visualizacao de tarefas rotineiras."""
    owner_name = serializers.CharField(source='owner.name', read_only=True)
    category_display = serializers.CharField(
        source='get_category_display', read_only=True
    )
    periodicity_display = serializers.CharField(
        source='get_periodicity_display', read_only=True
    )
    weekday_display = serializers.CharField(
        source='get_weekday_display', read_only=True
    )
    completion_rate = serializers.SerializerMethodField()
    total_completions = serializers.SerializerMethodField()

    class Meta:
        model = RoutineTask
        fields = [
            'id', 'uuid', 'name', 'description', 'category', 'category_display',
            'periodicity', 'periodicity_display', 'weekday', 'weekday_display',
            'day_of_month', 'is_active', 'target_quantity', 'unit',
            'completion_rate', 'total_completions',
            'owner', 'owner_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at']

    def get_completion_rate(self, obj):
        """Calcula taxa de cumprimento nos ultimos 30 dias."""
        from django.utils import timezone
        from datetime import timedelta

        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        records = obj.daily_records.filter(
            date__gte=thirty_days_ago,
            deleted_at__isnull=True
        )

        if records.count() == 0:
            return 0.0

        completed = records.filter(completed=True).count()
        return round((completed / records.count()) * 100, 1)

    def get_total_completions(self, obj):
        """Conta total de vezes que a tarefa foi cumprida."""
        return obj.daily_records.filter(
            completed=True,
            deleted_at__isnull=True
        ).count()


class RoutineTaskCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criacao/atualizacao de tarefas rotineiras."""
    class Meta:
        model = RoutineTask
        fields = [
            'id', 'name', 'description', 'category', 'periodicity',
            'weekday', 'day_of_month', 'is_active',
            'target_quantity', 'unit', 'owner'
        ]

    def validate(self, data):
        """Validacao customizada."""
        instance = RoutineTask(**data)
        instance.clean()
        return data


# ============================================================================
# DAILY TASK RECORD SERIALIZERS
# ============================================================================

class DailyTaskRecordSerializer(serializers.ModelSerializer):
    """Serializer para visualizacao de registros diarios."""
    owner_name = serializers.CharField(source='owner.name', read_only=True)
    task_name = serializers.CharField(source='task.name', read_only=True)
    task_category = serializers.CharField(source='task.category', read_only=True)
    task_target = serializers.IntegerField(source='task.target_quantity', read_only=True)
    task_unit = serializers.CharField(source='task.unit', read_only=True)

    class Meta:
        model = DailyTaskRecord
        fields = [
            'id', 'uuid', 'task', 'task_name', 'task_category',
            'task_target', 'task_unit', 'date', 'completed',
            'quantity_completed', 'notes', 'completed_at',
            'owner', 'owner_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['uuid', 'completed_at', 'created_at', 'updated_at']


class DailyTaskRecordCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criacao/atualizacao de registros diarios."""
    class Meta:
        model = DailyTaskRecord
        fields = [
            'id', 'task', 'date', 'completed',
            'quantity_completed', 'notes', 'owner'
        ]


# ============================================================================
# GOAL SERIALIZERS
# ============================================================================

class GoalSerializer(serializers.ModelSerializer):
    """Serializer para visualizacao de objetivos."""
    owner_name = serializers.CharField(source='owner.name', read_only=True)
    goal_type_display = serializers.CharField(
        source='get_goal_type_display', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    related_task_name = serializers.CharField(
        source='related_task.name', read_only=True
    )
    progress_percentage = serializers.ReadOnlyField()
    days_active = serializers.ReadOnlyField()

    class Meta:
        model = Goal
        fields = [
            'id', 'uuid', 'title', 'description', 'goal_type', 'goal_type_display',
            'related_task', 'related_task_name', 'target_value', 'current_value',
            'start_date', 'end_date', 'status', 'status_display',
            'progress_percentage', 'days_active',
            'owner', 'owner_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at']


class GoalCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criacao/atualizacao de objetivos."""
    class Meta:
        model = Goal
        fields = [
            'id', 'title', 'description', 'goal_type', 'related_task',
            'target_value', 'current_value', 'start_date', 'end_date',
            'status', 'owner'
        ]


# ============================================================================
# DAILY REFLECTION SERIALIZERS
# ============================================================================

class DailyReflectionSerializer(serializers.ModelSerializer):
    """Serializer para visualizacao de reflexoes diarias."""
    owner_name = serializers.CharField(source='owner.name', read_only=True)
    mood_display = serializers.CharField(source='get_mood_display', read_only=True)

    class Meta:
        model = DailyReflection
        fields = [
            'id', 'uuid', 'date', 'reflection', 'mood', 'mood_display',
            'owner', 'owner_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at']


class DailyReflectionCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criacao/atualizacao de reflexoes diarias."""
    class Meta:
        model = DailyReflection
        fields = ['id', 'date', 'reflection', 'mood', 'owner']
