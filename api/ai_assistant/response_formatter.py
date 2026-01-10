"""
Response Formatter for AI Assistant

Generates structured responses with visualizations based on intent classification.

Supported visualization types:
- cards: StatCards with key metrics
- chart: Line/Bar/Pie charts for trends and comparisons
- table: Tabular data for lists
- text: Plain text responses
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from django.db.models import Sum, Count, Avg, Max, Min
from django.db.models.functions import TruncMonth, TruncWeek


@dataclass
class FormattedResponse:
    """Structured response with visualization data."""
    response_type: str  # text, chart, cards, table
    answer: str  # Natural language answer
    visualization: Optional[Dict[str, Any]] = None
    sources: Optional[List[Dict]] = None


class ResponseFormatter:
    """
    Formats RAG results into structured responses with visualizations.

    Queries the database to generate appropriate visualizations
    based on the intent classification result.
    """

    def format_response(
        self,
        intent_result,
        rag_results: List,
        llm_answer: str,
        user_member
    ) -> FormattedResponse:
        """
        Format response based on intent and RAG results.

        Args:
            intent_result: IntentResult from IntentClassifier
            rag_results: List of SearchResult from RAG service
            llm_answer: Generated answer from LLM
            user_member: Member instance (authenticated user)

        Returns:
            FormattedResponse with visualization data
        """
        response_type = intent_result.response_type

        # Generate visualization if needed
        visualization = None
        if response_type == 'chart':
            visualization = self._generate_chart_data(
                intent_result, rag_results, user_member
            )
        elif response_type == 'cards':
            visualization = self._generate_cards_data(
                intent_result, rag_results, user_member
            )
        elif response_type == 'table':
            visualization = self._generate_table_data(
                intent_result, rag_results
            )

        # Format sources
        sources = [
            {
                'module': r.module,
                'type': r.entity_type,
                'score': round(r.score, 3),
                'metadata': r.metadata
            }
            for r in rag_results
        ]

        return FormattedResponse(
            response_type=response_type,
            answer=llm_answer,
            visualization=visualization,
            sources=sources
        )

    def _generate_chart_data(
        self,
        intent_result,
        rag_results: List,
        user_member
    ) -> Dict:
        """Generate chart configuration based on intent."""
        if intent_result.module == 'finance':
            if intent_result.intent_type == 'trend':
                return self._finance_trend_chart(intent_result, user_member)
            elif intent_result.intent_type == 'comparison':
                return self._finance_comparison_chart(intent_result, user_member)
            elif intent_result.intent_type == 'aggregation':
                return self._finance_aggregation_chart(intent_result, user_member)

        elif intent_result.module == 'library':
            if intent_result.intent_type == 'trend':
                return self._library_trend_chart(intent_result, user_member)

        # Default: empty chart
        return {
            'type': 'bar',
            'data': [],
            'config': {
                'dataKey': 'value',
                'nameKey': 'name'
            }
        }

    def _finance_trend_chart(self, intent_result, user_member) -> Dict:
        """Generate line chart for finance trends over time."""
        from expenses.models import Expense
        from revenues.models import Revenue

        date_range = intent_result.entities.get('date_range', {})

        # Get monthly expenses
        expense_query = Expense.objects.filter(
            member=user_member,
            deleted_at__isnull=True
        )

        if 'start' in date_range:
            expense_query = expense_query.filter(date__gte=date_range['start'])
        if 'end' in date_range:
            expense_query = expense_query.filter(date__lte=date_range['end'])

        monthly_expenses = expense_query.annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total=Sum('value')
        ).order_by('month')[:12]

        # Get monthly revenues
        revenue_query = Revenue.objects.filter(
            member=user_member,
            deleted_at__isnull=True
        )

        if 'start' in date_range:
            revenue_query = revenue_query.filter(date__gte=date_range['start'])
        if 'end' in date_range:
            revenue_query = revenue_query.filter(date__lte=date_range['end'])

        monthly_revenues = revenue_query.annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total=Sum('value')
        ).order_by('month')[:12]

        # Combine data
        data = []
        months = {}

        for exp in monthly_expenses:
            month_str = exp['month'].strftime('%b/%y')
            months[month_str] = {
                'name': month_str,
                'expenses': float(exp['total'] or 0),
                'revenues': 0
            }

        for rev in monthly_revenues:
            month_str = rev['month'].strftime('%b/%y')
            if month_str in months:
                months[month_str]['revenues'] = float(rev['total'] or 0)
            else:
                months[month_str] = {
                    'name': month_str,
                    'expenses': 0,
                    'revenues': float(rev['total'] or 0)
                }

        data = list(months.values())

        return {
            'type': 'line',
            'data': data,
            'config': {
                'dataKeys': ['expenses', 'revenues'],
                'nameKey': 'name',
                'withArea': True,
                'labels': {
                    'expenses': 'Despesas',
                    'revenues': 'Receitas'
                }
            }
        }

    def _finance_comparison_chart(self, intent_result, user_member) -> Dict:
        """Generate pie chart for category comparison."""
        from expenses.models import Expense

        date_range = intent_result.entities.get('date_range', {})
        limit = intent_result.entities.get('limit', 5)

        query = Expense.objects.filter(
            member=user_member,
            deleted_at__isnull=True
        )

        if 'start' in date_range:
            query = query.filter(date__gte=date_range['start'])
        if 'end' in date_range:
            query = query.filter(date__lte=date_range['end'])

        # Group by category
        by_category = query.values('category').annotate(
            total=Sum('value')
        ).order_by('-total')[:limit]

        data = [
            {
                'name': exp.get('category') or 'Outro',
                'value': float(exp['total'])
            }
            for exp in by_category
        ]

        return {
            'type': 'pie',
            'data': data,
            'config': {
                'dataKey': 'value',
                'nameKey': 'name'
            }
        }

    def _finance_aggregation_chart(self, intent_result, user_member) -> Dict:
        """Generate bar chart for top expenses/revenues."""
        from expenses.models import Expense

        date_range = intent_result.entities.get('date_range', {})
        limit = intent_result.entities.get('limit', 10)

        query = Expense.objects.filter(
            member=user_member,
            deleted_at__isnull=True
        )

        if 'start' in date_range:
            query = query.filter(date__gte=date_range['start'])
        if 'end' in date_range:
            query = query.filter(date__lte=date_range['end'])

        top_expenses = query.order_by('-value')[:limit]

        data = [
            {
                'name': exp.description[:30],  # Truncate long names
                'value': float(exp.value)
            }
            for exp in top_expenses
        ]

        return {
            'type': 'bar',
            'data': data,
            'config': {
                'dataKey': 'value',
                'nameKey': 'name',
                'layout': 'horizontal'
            }
        }

    def _library_trend_chart(self, intent_result, user_member) -> Dict:
        """Generate line chart for reading trends."""
        from library.models import Reading

        # Get reading activity over time
        readings = Reading.objects.filter(
            owner=user_member,
            deleted_at__isnull=True
        ).annotate(
            week=TruncWeek('reading_date')
        ).values('week').annotate(
            pages=Sum('pages_read'),
            sessions=Count('id')
        ).order_by('week')[:12]

        data = [
            {
                'name': r['week'].strftime('%d/%m'),
                'pages': r['pages'],
                'sessions': r['sessions']
            }
            for r in readings
        ]

        return {
            'type': 'line',
            'data': data,
            'config': {
                'dataKeys': ['pages', 'sessions'],
                'nameKey': 'name',
                'withArea': False,
                'labels': {
                    'pages': 'Páginas lidas',
                    'sessions': 'Sessões de leitura'
                }
            }
        }

    def _generate_cards_data(
        self,
        intent_result,
        rag_results: List,
        user_member
    ) -> Dict:
        """Generate stat cards data based on module."""
        if intent_result.module == 'finance':
            return self._finance_stat_cards(intent_result, user_member)
        elif intent_result.module == 'security':
            return self._security_stat_cards(user_member)
        elif intent_result.module == 'library':
            return self._library_stat_cards(user_member)
        elif intent_result.module == 'planning':
            return self._planning_stat_cards(user_member)

        return {
            'type': 'stat_cards',
            'cards': []
        }

    def _finance_stat_cards(self, intent_result, user_member) -> Dict:
        """Generate finance stat cards."""
        from expenses.models import Expense
        from revenues.models import Revenue
        from accounts.models import Account

        date_range = intent_result.entities.get('date_range', {})

        # Build queries
        expense_query = Expense.objects.filter(
            member=user_member,
            deleted_at__isnull=True
        )
        revenue_query = Revenue.objects.filter(
            member=user_member,
            deleted_at__isnull=True
        )

        if 'start' in date_range:
            expense_query = expense_query.filter(date__gte=date_range['start'])
            revenue_query = revenue_query.filter(date__gte=date_range['start'])
        if 'end' in date_range:
            expense_query = expense_query.filter(date__lte=date_range['end'])
            revenue_query = revenue_query.filter(date__lte=date_range['end'])

        # Calculate totals
        total_expenses = expense_query.aggregate(total=Sum('value'))['total'] or 0
        total_revenues = revenue_query.aggregate(total=Sum('value'))['total'] or 0
        balance = float(total_revenues) - float(total_expenses)

        # Get total account balance
        account_balance = Account.objects.filter(
            owner=user_member,
            is_deleted=False,
            is_active=True
        ).aggregate(total=Sum('current_balance'))['total'] or 0

        period_label = date_range.get('label', '')

        return {
            'type': 'stat_cards',
            'cards': [
                {
                    'title': f'Despesas {period_label}' if period_label else 'Despesas',
                    'value': f'R$ {float(total_expenses):,.2f}',
                    'variant': 'danger'
                },
                {
                    'title': f'Receitas {period_label}' if period_label else 'Receitas',
                    'value': f'R$ {float(total_revenues):,.2f}',
                    'variant': 'success'
                },
                {
                    'title': f'Saldo {period_label}' if period_label else 'Saldo Geral',
                    'value': f'R$ {balance:,.2f}',
                    'variant': 'default' if balance >= 0 else 'danger'
                }
            ]
        }

    def _security_stat_cards(self, user_member) -> Dict:
        """Generate security module stat cards."""
        from security.models import Password, StoredCreditCard, Archive

        password_count = Password.objects.filter(
            owner=user_member,
            deleted_at__isnull=True
        ).count()

        card_count = StoredCreditCard.objects.filter(
            owner=user_member,
            deleted_at__isnull=True
        ).count()

        archive_count = Archive.objects.filter(
            owner=user_member,
            deleted_at__isnull=True
        ).count()

        return {
            'type': 'stat_cards',
            'cards': [
                {
                    'title': 'Senhas Armazenadas',
                    'value': str(password_count),
                    'variant': 'default'
                },
                {
                    'title': 'Cartões Salvos',
                    'value': str(card_count),
                    'variant': 'default'
                },
                {
                    'title': 'Arquivos Seguros',
                    'value': str(archive_count),
                    'variant': 'default'
                }
            ]
        }

    def _library_stat_cards(self, user_member) -> Dict:
        """Generate library module stat cards."""
        from library.models import Book, Reading

        total_books = Book.objects.filter(
            owner=user_member,
            deleted_at__isnull=True
        ).count()

        read_books = Book.objects.filter(
            owner=user_member,
            deleted_at__isnull=True,
            read_status='read'
        ).count()

        total_pages = Reading.objects.filter(
            owner=user_member,
            deleted_at__isnull=True
        ).aggregate(total=Sum('pages_read'))['total'] or 0

        return {
            'type': 'stat_cards',
            'cards': [
                {
                    'title': 'Total de Livros',
                    'value': str(total_books),
                    'variant': 'default'
                },
                {
                    'title': 'Livros Lidos',
                    'value': str(read_books),
                    'variant': 'success'
                },
                {
                    'title': 'Páginas Lidas',
                    'value': str(total_pages),
                    'variant': 'default'
                }
            ]
        }

    def _planning_stat_cards(self, user_member) -> Dict:
        """Generate planning module stat cards."""
        from personal_planning.models import RoutineTask, DailyTaskRecord, Goal

        active_tasks = RoutineTask.objects.filter(
            owner=user_member,
            deleted_at__isnull=True,
            is_active=True
        ).count()

        today = datetime.now().date()
        completed_today = DailyTaskRecord.objects.filter(
            owner=user_member,
            deleted_at__isnull=True,
            date=today,
            completed=True
        ).count()

        active_goals = Goal.objects.filter(
            owner=user_member,
            deleted_at__isnull=True,
            status='active'
        ).count()

        return {
            'type': 'stat_cards',
            'cards': [
                {
                    'title': 'Tarefas Ativas',
                    'value': str(active_tasks),
                    'variant': 'default'
                },
                {
                    'title': 'Completadas Hoje',
                    'value': str(completed_today),
                    'variant': 'success'
                },
                {
                    'title': 'Objetivos Ativos',
                    'value': str(active_goals),
                    'variant': 'default'
                }
            ]
        }

    def _generate_table_data(
        self,
        intent_result,
        rag_results: List
    ) -> Dict:
        """Generate table data from RAG results."""
        # Convert RAG results to table rows
        rows = []
        for r in rag_results[:15]:  # Limit to 15 rows
            row = {
                'module': r.module,
                'type': r.entity_type,
            }

            # Extract key fields from metadata
            metadata = r.metadata
            if 'title' in metadata:
                row['description'] = metadata['title']
            elif 'name' in metadata:
                row['description'] = metadata['name']
            elif 'description' in metadata:
                row['description'] = metadata['description']
            else:
                row['description'] = 'N/A'

            row['value'] = metadata.get('value', 'N/A')
            row['date'] = metadata.get('date', 'N/A')

            rows.append(row)

        return {
            'type': 'table',
            'columns': [
                {'key': 'module', 'label': 'Módulo'},
                {'key': 'type', 'label': 'Tipo'},
                {'key': 'description', 'label': 'Descrição'},
                {'key': 'value', 'label': 'Valor'},
                {'key': 'date', 'label': 'Data'}
            ],
            'rows': rows
        }


# Singleton instance
_response_formatter: Optional[ResponseFormatter] = None


def get_response_formatter() -> ResponseFormatter:
    """
    Get the singleton ResponseFormatter instance.

    Returns:
        The global ResponseFormatter instance
    """
    global _response_formatter
    if _response_formatter is None:
        _response_formatter = ResponseFormatter()
    return _response_formatter
