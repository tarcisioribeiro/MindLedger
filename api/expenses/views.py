from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django_filters import rest_framework as filters
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from calendar import monthrange
from expenses.models import Expense, FixedExpense, FixedExpenseGenerationLog
from expenses.serializers import (
    ExpenseSerializer,
    FixedExpenseSerializer,
    FixedExpenseCreateUpdateSerializer,
    BulkGenerateRequestSerializer,
    BulkGenerateResponseSerializer,
    BulkMarkPaidSerializer
)
from expenses.filters import ExpenseFilter
from app.permissions import GlobalDefaultPermission


class ExpenseCreateListView(generics.ListCreateAPIView):
    """
    ViewSet para listar e criar despesas.

    Permite:
    - GET: Lista todas as despesas ordenadas por data decrescente
    - POST: Cria uma nova despesa

    Attributes
    ----------
    permission_classes : tuple
        Permissões necessárias (IsAuthenticated, GlobalDefaultPermission)
    queryset : QuerySet
        QuerySet de todas as despesas (exclui deletadas) com relação account pré-carregada
    serializer_class : class
        Serializer usado para validação e serialização
    filter_backends : list
        Backends de filtro (DjangoFilterBackend)
    filterset_class : class
        Classe de filtros personalizada para despesas
    ordering : list
        Ordenação padrão por data e ID decrescente
    """
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = Expense.objects.filter(is_deleted=False).select_related('account')
    serializer_class = ExpenseSerializer
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = ExpenseFilter
    ordering = ['-date', '-id']  # Consistent ordering for pagination


class ExpenseRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    ViewSet para operações individuais em despesas.

    Permite:
    - GET: Recupera uma despesa específica
    - PUT/PATCH: Atualiza uma despesa existente
    - DELETE: Remove uma despesa

    Attributes
    ----------
    permission_classes : tuple
        Permissões necessárias (IsAuthenticated, GlobalDefaultPermission)
    queryset : QuerySet
        QuerySet de todas as despesas (exclui deletadas) com relação account pré-carregada
    serializer_class : class
        Serializer usado para validação e serialização
    """
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = Expense.objects.filter(is_deleted=False).select_related('account')
    serializer_class = ExpenseSerializer


# Fixed Expense Views

class FixedExpenseListCreateView(generics.ListCreateAPIView):
    """
    View para listar e criar templates de despesas fixas.

    GET: Lista todas as despesas fixas ativas
    POST: Cria um novo template de despesa fixa
    """
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = FixedExpense.objects.all()  # Required for GlobalDefaultPermission

    def get_queryset(self):
        return FixedExpense.objects.filter(
            is_deleted=False
        ).select_related('account', 'member').annotate(
            total_generated=Count('generated_expenses')
        ).order_by('due_day', 'description')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return FixedExpenseCreateUpdateSerializer
        return FixedExpenseSerializer

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )


class FixedExpenseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View para operações individuais em templates de despesas fixas.

    GET: Recupera um template específico
    PUT/PATCH: Atualiza um template existente
    DELETE: Remove um template (soft delete)
    """
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = FixedExpense.objects.filter(is_deleted=False).select_related('account', 'member')

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return FixedExpenseCreateUpdateSerializer
        return FixedExpenseSerializer

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        # Soft delete
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()


class BulkGenerateFixedExpensesView(APIView):
    """
    View para geração em lote de despesas fixas.

    POST: Gera todas as despesas fixas para um mês específico
    """
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = FixedExpense.objects.none()  # Required for GlobalDefaultPermission

    def post(self, request):
        serializer = BulkGenerateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        month = serializer.validated_data['month']
        expense_values = serializer.validated_data['expense_values']

        # Verificar se já foi gerado para este mês
        if FixedExpenseGenerationLog.objects.filter(month=month, is_deleted=False).exists():
            return Response({
                'error': f'Despesas fixas já foram geradas para {month}'
            }, status=status.HTTP_400_BAD_REQUEST)

        created_expenses = []
        year, month_num = month.split('-')
        fixed_expense_ids = []

        try:
            for item in expense_values:
                fixed_exp = FixedExpense.objects.get(
                    id=item['fixed_expense_id'],
                    is_deleted=False,
                    is_active=True
                )
                fixed_expense_ids.append(fixed_exp.id)

                # Calcular data da despesa (year-month + due_day)
                try:
                    expense_date = datetime(int(year), int(month_num), fixed_exp.due_day).date()
                except ValueError:
                    # Tratar datas inválidas (ex: 31/Fev -> último dia de Fev)
                    last_day = monthrange(int(year), int(month_num))[1]
                    expense_date = datetime(int(year), int(month_num), min(fixed_exp.due_day, last_day)).date()

                # Criar despesa
                expense = Expense.objects.create(
                    description=fixed_exp.description,
                    value=item['value'],
                    date=expense_date,
                    horary=timezone.now().time(),
                    category=fixed_exp.category,
                    account=fixed_exp.account,
                    payed=False,
                    merchant=fixed_exp.merchant,
                    payment_method=fixed_exp.payment_method,
                    notes=fixed_exp.notes,
                    member=fixed_exp.member,
                    fixed_expense_template=fixed_exp,
                    created_by=request.user,
                    updated_by=request.user
                )
                created_expenses.append(expense)

                # Atualizar last_generated_month no template
                fixed_exp.last_generated_month = month
                fixed_exp.save()

            # Criar log de geração
            FixedExpenseGenerationLog.objects.create(
                month=month,
                generated_by=request.user,
                total_generated=len(created_expenses),
                fixed_expense_ids=fixed_expense_ids,
                created_by=request.user,
                updated_by=request.user
            )

            # Serializar resposta
            response_data = {
                'success': True,
                'created_count': len(created_expenses),
                'month': month,
                'expenses': created_expenses
            }
            response_serializer = BulkGenerateResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except FixedExpense.DoesNotExist:
            return Response({
                'error': 'Uma ou mais despesas fixas não foram encontradas ou estão inativas'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Erro ao gerar despesas: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BulkMarkPaidView(APIView):
    """
    View para marcar múltiplas despesas como pagas.

    POST: Marca todas as despesas especificadas como pagas
    """
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = Expense.objects.none()  # Required for GlobalDefaultPermission

    def post(self, request):
        serializer = BulkMarkPaidSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        expense_ids = serializer.validated_data['expense_ids']

        updated = Expense.objects.filter(
            id__in=expense_ids,
            is_deleted=False
        ).update(
            payed=True,
            updated_by=request.user
        )

        return Response({
            'success': True,
            'updated_count': updated
        }, status=status.HTTP_200_OK)


class FixedExpensesStatsView(APIView):
    """
    View para estatísticas de despesas fixas.

    GET: Retorna estatísticas consolidadas sobre despesas fixas
    """
    permission_classes = (IsAuthenticated, GlobalDefaultPermission,)
    queryset = FixedExpense.objects.none()  # Required for GlobalDefaultPermission

    def get(self, request):
        now = timezone.now()
        current_month = now.strftime('%Y-%m')
        previous_date = now - timedelta(days=30)
        previous_month = previous_date.strftime('%Y-%m')

        # Templates ativos
        active_templates = FixedExpense.objects.filter(
            is_active=True,
            is_deleted=False
        ).count()

        # Despesas do mês atual
        year, month = current_month.split('-')
        month_start = datetime(int(year), int(month), 1).date()
        last_day = monthrange(int(year), int(month))[1]
        month_end = datetime(int(year), int(month), last_day).date()

        current_expenses = Expense.objects.filter(
            fixed_expense_template__isnull=False,
            date__gte=month_start,
            date__lte=month_end,
            is_deleted=False
        )

        current_total = current_expenses.aggregate(Sum('value'))['value__sum'] or 0
        current_paid = current_expenses.filter(payed=True).count()
        current_pending = current_expenses.filter(payed=False).count()

        # Despesas do mês anterior
        prev_year, prev_month_num = previous_month.split('-')
        prev_start = datetime(int(prev_year), int(prev_month_num), 1).date()
        prev_last_day = monthrange(int(prev_year), int(prev_month_num))[1]
        prev_end = datetime(int(prev_year), int(prev_month_num), prev_last_day).date()

        previous_total = Expense.objects.filter(
            fixed_expense_template__isnull=False,
            date__gte=prev_start,
            date__lte=prev_end,
            is_deleted=False
        ).aggregate(Sum('value'))['value__sum'] or 0

        # Breakdown por categoria
        category_breakdown = list(current_expenses.values('category').annotate(
            total=Sum('value'),
            count=Count('id')
        ).order_by('-total'))

        # Calcular diferença e percentual
        difference = float(current_total) - float(previous_total)
        percentage_change = 0
        if previous_total > 0:
            percentage_change = (difference / float(previous_total)) * 100

        return Response({
            'active_templates': active_templates,
            'current_month': {
                'month': current_month,
                'total_value': float(current_total),
                'paid_count': current_paid,
                'pending_count': current_pending,
                'total_count': current_paid + current_pending
            },
            'previous_month': {
                'month': previous_month,
                'total_value': float(previous_total)
            },
            'comparison': {
                'difference': difference,
                'percentage_change': round(percentage_change, 2)
            },
            'category_breakdown': category_breakdown
        }, status=status.HTTP_200_OK)
