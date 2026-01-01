from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta, date
from app.permissions import GlobalDefaultPermission
from personal_planning.models import (
    RoutineTask, DailyTaskRecord, Goal, DailyReflection
)
from personal_planning.serializers import (
    RoutineTaskSerializer, RoutineTaskCreateUpdateSerializer,
    DailyTaskRecordSerializer, DailyTaskRecordCreateUpdateSerializer,
    GoalSerializer, GoalCreateUpdateSerializer,
    DailyReflectionSerializer, DailyReflectionCreateUpdateSerializer
)


def log_activity(request, action, model_name, object_id, description):
    """Helper para registrar atividades."""
    try:
        from security.activity_logs.models import ActivityLog
        ActivityLog.log_action(
            user=request.user,
            action=action,
            description=description,
            model_name=model_name,
            object_id=object_id,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    except Exception:
        pass


def get_client_ip(request):
    """Extrai o IP do cliente."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ============================================================================
# ROUTINE TASK VIEWS
# ============================================================================

class RoutineTaskListCreateView(generics.ListCreateAPIView):
    """Lista todas as tarefas rotineiras ou cria uma nova."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    queryset = RoutineTask.objects.all()

    def get_queryset(self):
        return RoutineTask.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        ).select_related('owner').prefetch_related('daily_records', 'goals')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RoutineTaskCreateUpdateSerializer
        return RoutineTaskSerializer

    def perform_create(self, serializer):
        task = serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
        log_activity(
            self.request, 'create', 'RoutineTask',
            task.id, f'Criou tarefa rotineira: {task.name}'
        )


class RoutineTaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Recupera, atualiza ou deleta uma tarefa rotineira."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    queryset = RoutineTask.objects.all()

    def get_queryset(self):
        return RoutineTask.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        ).select_related('owner').prefetch_related('daily_records', 'goals')

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return RoutineTaskCreateUpdateSerializer
        return RoutineTaskSerializer

    def perform_update(self, serializer):
        task = serializer.save(updated_by=self.request.user)
        log_activity(
            self.request, 'update', 'RoutineTask',
            task.id, f'Atualizou tarefa rotineira: {task.name}'
        )

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()
        log_activity(
            self.request, 'delete', 'RoutineTask',
            instance.id, f'Deletou tarefa rotineira: {instance.name}'
        )


# ============================================================================
# DAILY TASK RECORD VIEWS
# ============================================================================

class DailyTaskRecordListCreateView(generics.ListCreateAPIView):
    """Lista todos os registros diarios ou cria um novo."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    queryset = DailyTaskRecord.objects.all()

    def get_queryset(self):
        return DailyTaskRecord.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        ).select_related('owner', 'task')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DailyTaskRecordCreateUpdateSerializer
        return DailyTaskRecordSerializer

    def perform_create(self, serializer):
        record = serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
        log_activity(
            self.request, 'create', 'DailyTaskRecord',
            record.id, f'Registrou tarefa: {record.task.name} em {record.date}'
        )


class DailyTaskRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Recupera, atualiza ou deleta um registro diario."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    queryset = DailyTaskRecord.objects.all()

    def get_queryset(self):
        return DailyTaskRecord.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        ).select_related('owner', 'task')

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return DailyTaskRecordCreateUpdateSerializer
        return DailyTaskRecordSerializer

    def perform_update(self, serializer):
        record = serializer.save(updated_by=self.request.user)
        log_activity(
            self.request, 'update', 'DailyTaskRecord',
            record.id, f'Atualizou registro de: {record.task.name}'
        )

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()
        log_activity(
            self.request, 'delete', 'DailyTaskRecord',
            instance.id, f'Deletou registro de: {instance.task.name}'
        )


# ============================================================================
# TASKS FOR TODAY VIEW (Endpoint Especial)
# ============================================================================

class TasksForTodayView(APIView):
    """
    GET /api/v1/personal-planning/tasks-today/

    Retorna todas as tarefas que devem ser cumpridas hoje,
    junto com o status de cumprimento (se ja existe registro).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()

        # Query parameter para data customizada (opcional)
        date_param = request.query_params.get('date')
        if date_param:
            try:
                today = date.fromisoformat(date_param)
            except ValueError:
                pass

        # Buscar todas as tarefas ativas do usuario
        active_tasks = RoutineTask.objects.filter(
            owner__user=user,
            is_active=True,
            deleted_at__isnull=True
        )

        # Filtrar tarefas que devem aparecer hoje
        tasks_for_today = []
        for task in active_tasks:
            if task.should_appear_on_date(today):
                # Verificar se ja existe registro para hoje
                record = DailyTaskRecord.objects.filter(
                    task=task,
                    date=today,
                    owner=task.owner,
                    deleted_at__isnull=True
                ).first()

                tasks_for_today.append({
                    'task_id': task.id,
                    'task_name': task.name,
                    'category': task.category,
                    'category_display': task.get_category_display(),
                    'target_quantity': task.target_quantity,
                    'unit': task.unit,
                    'record_id': record.id if record else None,
                    'completed': record.completed if record else False,
                    'quantity_completed': record.quantity_completed if record else 0,
                    'notes': record.notes if record else None
                })

        return Response({
            'date': today.isoformat(),
            'tasks': tasks_for_today,
            'total_tasks': len(tasks_for_today),
            'completed_tasks': len([t for t in tasks_for_today if t['completed']])
        })


# ============================================================================
# GOAL VIEWS
# ============================================================================

class GoalListCreateView(generics.ListCreateAPIView):
    """Lista todos os objetivos ou cria um novo."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    queryset = Goal.objects.all()

    def get_queryset(self):
        return Goal.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        ).select_related('owner', 'related_task')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return GoalCreateUpdateSerializer
        return GoalSerializer

    def perform_create(self, serializer):
        goal = serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
        log_activity(
            self.request, 'create', 'Goal',
            goal.id, f'Criou objetivo: {goal.title}'
        )


class GoalDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Recupera, atualiza ou deleta um objetivo."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    queryset = Goal.objects.all()

    def get_queryset(self):
        return Goal.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        ).select_related('owner', 'related_task')

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return GoalCreateUpdateSerializer
        return GoalSerializer

    def perform_update(self, serializer):
        goal = serializer.save(updated_by=self.request.user)
        log_activity(
            self.request, 'update', 'Goal',
            goal.id, f'Atualizou objetivo: {goal.title}'
        )

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()
        log_activity(
            self.request, 'delete', 'Goal',
            instance.id, f'Deletou objetivo: {instance.title}'
        )


# ============================================================================
# DAILY REFLECTION VIEWS
# ============================================================================

class DailyReflectionListCreateView(generics.ListCreateAPIView):
    """Lista todas as reflexoes diarias ou cria uma nova."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    queryset = DailyReflection.objects.all()

    def get_queryset(self):
        return DailyReflection.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        ).select_related('owner')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DailyReflectionCreateUpdateSerializer
        return DailyReflectionSerializer

    def perform_create(self, serializer):
        reflection = serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
        log_activity(
            self.request, 'create', 'DailyReflection',
            reflection.id, f'Criou reflexao de {reflection.date}'
        )


class DailyReflectionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Recupera, atualiza ou deleta uma reflexao diaria."""
    permission_classes = [IsAuthenticated, GlobalDefaultPermission]
    queryset = DailyReflection.objects.all()

    def get_queryset(self):
        return DailyReflection.objects.filter(
            owner__user=self.request.user,
            deleted_at__isnull=True
        ).select_related('owner')

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return DailyReflectionCreateUpdateSerializer
        return DailyReflectionSerializer

    def perform_update(self, serializer):
        reflection = serializer.save(updated_by=self.request.user)
        log_activity(
            self.request, 'update', 'DailyReflection',
            reflection.id, f'Atualizou reflexao de {reflection.date}'
        )

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()
        log_activity(
            self.request, 'delete', 'DailyReflection',
            instance.id, f'Deletou reflexao de {instance.date}'
        )


# ============================================================================
# DASHBOARD STATS VIEW
# ============================================================================

class PersonalPlanningDashboardStatsView(APIView):
    """
    GET /api/v1/personal-planning/dashboard/stats/

    Retorna estatisticas agregadas do modulo de Planejamento Pessoal.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()

        # Querysets filtrados
        tasks_qs = RoutineTask.objects.filter(
            owner__user=user,
            deleted_at__isnull=True
        )
        records_qs = DailyTaskRecord.objects.filter(
            owner__user=user,
            deleted_at__isnull=True
        )
        goals_qs = Goal.objects.filter(
            owner__user=user,
            deleted_at__isnull=True
        )

        # Contadores gerais
        total_tasks = tasks_qs.count()
        active_tasks = tasks_qs.filter(is_active=True).count()
        total_goals = goals_qs.count()
        active_goals = goals_qs.filter(status='active').count()
        completed_goals = goals_qs.filter(status='completed').count()

        # Taxa de cumprimento dos ultimos 7 dias
        seven_days_ago = today - timedelta(days=7)
        recent_records = records_qs.filter(date__gte=seven_days_ago)
        total_recent = recent_records.count()
        completed_recent = recent_records.filter(completed=True).count()
        completion_rate_7d = (
            round((completed_recent / total_recent) * 100, 1)
            if total_recent > 0 else 0.0
        )

        # Taxa de cumprimento dos ultimos 30 dias
        thirty_days_ago = today - timedelta(days=30)
        month_records = records_qs.filter(date__gte=thirty_days_ago)
        total_month = month_records.count()
        completed_month = month_records.filter(completed=True).count()
        completion_rate_30d = (
            round((completed_month / total_month) * 100, 1)
            if total_month > 0 else 0.0
        )

        # Tarefas por categoria (Top 5)
        tasks_by_category = list(
            tasks_qs.filter(is_active=True)
            .values('category')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

        # Adicionar display name
        from personal_planning.models import TASK_CATEGORY_CHOICES
        category_dict = dict(TASK_CATEGORY_CHOICES)
        for item in tasks_by_category:
            item['category_display'] = category_dict.get(
                item['category'], item['category']
            )

        # Progresso semanal (ultimos 7 dias)
        weekly_progress = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_records = records_qs.filter(date=day)
            total_day = day_records.count()
            completed_day = day_records.filter(completed=True).count()

            weekly_progress.append({
                'date': day.isoformat(),
                'total': total_day,
                'completed': completed_day,
                'rate': round((completed_day / total_day) * 100, 1) if total_day > 0 else 0
            })

        # Objetivos ativos com progresso
        active_goals_data = []
        for goal in goals_qs.filter(status='active')[:5]:
            active_goals_data.append({
                'title': goal.title,
                'progress_percentage': round(goal.progress_percentage, 1),
                'current_value': goal.current_value,
                'target_value': goal.target_value,
                'days_active': goal.days_active
            })

        # Streak atual (dias consecutivos cumprindo todas as tarefas)
        current_streak = self._calculate_current_streak(user, today)

        # Melhor streak
        best_streak = self._calculate_best_streak(user)

        stats = {
            'total_tasks': total_tasks,
            'active_tasks': active_tasks,
            'total_goals': total_goals,
            'active_goals': active_goals,
            'completed_goals': completed_goals,
            'completion_rate_7d': completion_rate_7d,
            'completion_rate_30d': completion_rate_30d,
            'current_streak': current_streak,
            'best_streak': best_streak,
            'tasks_by_category': tasks_by_category,
            'weekly_progress': weekly_progress,
            'active_goals_progress': active_goals_data
        }

        return Response(stats)

    def _calculate_current_streak(self, user, today):
        """Calcula sequencia atual de dias com 100% de cumprimento."""
        streak = 0
        check_date = today

        while True:
            # Buscar tarefas do dia
            active_tasks = RoutineTask.objects.filter(
                owner__user=user,
                is_active=True,
                deleted_at__isnull=True
            )

            tasks_for_day = [
                t for t in active_tasks
                if t.should_appear_on_date(check_date)
            ]

            if not tasks_for_day:
                # Se nao ha tarefas para o dia, nao quebra o streak
                check_date -= timedelta(days=1)
                continue

            # Verificar se todas foram cumpridas
            records = DailyTaskRecord.objects.filter(
                owner__user=user,
                date=check_date,
                deleted_at__isnull=True
            )

            completed_tasks = records.filter(completed=True).count()

            if completed_tasks == len(tasks_for_day):
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break

        return streak

    def _calculate_best_streak(self, user):
        """Calcula a melhor sequencia de todos os tempos."""
        # Implementacao simplificada - pode ser otimizada
        # Buscar todos os registros e calcular a melhor sequencia
        records = DailyTaskRecord.objects.filter(
            owner__user=user,
            deleted_at__isnull=True
        ).order_by('date')

        if not records:
            return 0

        # Logica para calcular melhor streak (simplificada)
        best = 0
        current = 0
        last_date = None

        for record in records:
            if last_date and (record.date - last_date).days == 1:
                if record.completed:
                    current += 1
                    best = max(best, current)
                else:
                    current = 0
            else:
                current = 1 if record.completed else 0

            last_date = record.date

        return best
