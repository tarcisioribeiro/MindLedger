"""
Query Result Formatter for AI Assistant.

Formats SQL query results into structured responses with visualizations.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from decimal import Decimal

from .executor import QueryResult
from .generator import SQLGenerationResult
from .prompts import get_answer_generation_prompt


logger = logging.getLogger(__name__)


@dataclass
class FormattedQueryResponse:
    """Formatted response from SQL query."""
    summary: str
    data: List[Dict[str, Any]]
    totals: Optional[Dict[str, Any]]
    sql_query: str
    sql_explanation: str
    visualization: Optional[Dict[str, Any]]
    row_count: int
    truncated: bool
    execution_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class QueryResultFormatter:
    """
    Formats query results for structured responses.

    Generates:
    - Natural language summary
    - Data tables
    - Totals and aggregations
    - Visualizations (charts, cards, tables)
    - SQL display
    """

    def __init__(self):
        """Initialize the formatter."""
        self._llm_provider = None

    def _get_llm_provider(self):
        """Lazy-load the LLM provider."""
        if self._llm_provider is None:
            from ..llm_router.providers.groq import GroqProvider
            self._llm_provider = GroqProvider()
        return self._llm_provider

    def format(
        self,
        query_result: QueryResult,
        generation_result: SQLGenerationResult,
        question: str,
        generate_summary: bool = True
    ) -> FormattedQueryResponse:
        """
        Format query results into structured response.

        Args:
            query_result: Result from query execution
            generation_result: Result from SQL generation
            question: Original user question
            generate_summary: Whether to generate LLM summary

        Returns:
            FormattedQueryResponse with all components
        """
        # Convert rows to dict list
        data = query_result.to_dict_list()

        # Calculate totals if applicable
        totals = self._calculate_totals(data, generation_result.query_type)

        # Generate visualization
        visualization = self._generate_visualization(
            data=data,
            query_type=generation_result.query_type,
            module=generation_result.module,
            columns=query_result.columns
        )

        # Generate summary
        if generate_summary and query_result.row_count > 0:
            summary = self._generate_summary(
                question=question,
                sql=query_result.sql,
                data=data,
                row_count=query_result.row_count
            )
        elif query_result.row_count == 0:
            summary = self._generate_empty_response(question)
        else:
            summary = self._generate_basic_summary(data, question)

        return FormattedQueryResponse(
            summary=summary,
            data=data,
            totals=totals,
            sql_query=query_result.sql,
            sql_explanation=generation_result.explanation or "",
            visualization=visualization,
            row_count=query_result.row_count,
            truncated=query_result.truncated,
            execution_time_ms=query_result.execution_time_ms,
            metadata={
                'query_type': generation_result.query_type,
                'module': generation_result.module,
                'tables': generation_result.tables_detected,
                'confidence': generation_result.confidence,
            }
        )

    def _calculate_totals(
        self,
        data: List[Dict[str, Any]],
        query_type: str
    ) -> Optional[Dict[str, Any]]:
        """Calculate totals from data if applicable."""
        if not data:
            return None

        totals = {}

        # Identify numeric columns
        numeric_cols = []
        for col, value in data[0].items():
            if isinstance(value, (int, float, Decimal)) and col not in ('id', 'count'):
                numeric_cols.append(col)

        # Calculate sums for numeric columns
        for col in numeric_cols:
            values = [row.get(col, 0) or 0 for row in data]
            col_sum = sum(values)
            if col_sum > 0:
                totals[f'{col}_total'] = col_sum
                totals[f'{col}_avg'] = col_sum / len(data)

        # Count total rows
        totals['row_count'] = len(data)

        return totals if totals else None

    def _generate_visualization(
        self,
        data: List[Dict[str, Any]],
        query_type: str,
        module: str,
        columns: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Generate visualization configuration based on query type."""
        if not data:
            return None

        # Determine visualization type
        if query_type == 'trend':
            return self._generate_chart_visualization(data, columns, 'line')
        elif query_type == 'comparison':
            return self._generate_chart_visualization(data, columns, 'bar')
        elif query_type == 'aggregation':
            return self._generate_cards_visualization(data, columns)
        else:
            return self._generate_table_visualization(data, columns)

    def _generate_chart_visualization(
        self,
        data: List[Dict[str, Any]],
        columns: List[str],
        chart_type: str
    ) -> Dict[str, Any]:
        """Generate chart visualization config."""
        # Find date/period column for X-axis
        x_col = None
        for col in columns:
            if col in ('mes', 'month', 'date', 'dia', 'semana', 'ano', 'year'):
                x_col = col
                break

        if not x_col and columns:
            x_col = columns[0]

        # Find numeric columns for Y-axis
        y_cols = []
        for col in columns:
            if col != x_col:
                sample_val = data[0].get(col) if data else None
                if isinstance(sample_val, (int, float, Decimal)):
                    y_cols.append(col)

        return {
            'type': 'chart',
            'chart_type': chart_type,
            'x_axis': x_col,
            'y_axes': y_cols or [columns[1]] if len(columns) > 1 else [],
            'data': data,
            'title': self._get_chart_title(columns),
        }

    def _generate_cards_visualization(
        self,
        data: List[Dict[str, Any]],
        columns: List[str]
    ) -> Dict[str, Any]:
        """Generate cards visualization for aggregations."""
        cards = []

        if len(data) == 1:
            # Single row - show each value as a card
            row = data[0]
            for col, value in row.items():
                if col not in ('id',):
                    cards.append({
                        'label': self._format_column_name(col),
                        'value': self._format_value_for_display(value, col),
                        'raw_value': value,
                    })
        else:
            # Multiple rows - summarize
            for col in columns:
                if col in ('id',):
                    continue

                values = [row.get(col) for row in data if row.get(col) is not None]
                if values and isinstance(values[0], (int, float, Decimal)):
                    total = sum(values)
                    cards.append({
                        'label': f'Total {self._format_column_name(col)}',
                        'value': self._format_value_for_display(total, col),
                        'raw_value': total,
                    })

        return {
            'type': 'cards',
            'cards': cards,
        }

    def _generate_table_visualization(
        self,
        data: List[Dict[str, Any]],
        columns: List[str]
    ) -> Dict[str, Any]:
        """Generate table visualization."""
        # Format columns for display
        formatted_columns = [
            {
                'key': col,
                'label': self._format_column_name(col),
                'align': 'right' if self._is_numeric_column(data, col) else 'left',
            }
            for col in columns
            if col not in ('id', 'uuid', 'deleted_at', 'is_deleted')
        ]

        # Format data for display
        formatted_data = []
        for row in data:
            formatted_row = {}
            for col in columns:
                if col not in ('id', 'uuid', 'deleted_at', 'is_deleted'):
                    formatted_row[col] = self._format_value_for_display(
                        row.get(col), col
                    )
            formatted_data.append(formatted_row)

        return {
            'type': 'table',
            'columns': formatted_columns,
            'data': formatted_data,
            'row_count': len(data),
        }

    def _generate_summary(
        self,
        question: str,
        sql: str,
        data: List[Dict[str, Any]],
        row_count: int
    ) -> str:
        """Generate natural language summary using LLM."""
        try:
            # Format results for prompt
            results_text = self._format_results_for_prompt(data, max_rows=20)

            # Build prompt
            prompt = get_answer_generation_prompt(
                question=question,
                sql=sql,
                results=results_text,
                row_count=row_count
            )

            # Generate summary
            provider = self._get_llm_provider()
            result = provider.generate(
                prompt=prompt,
                system="Voce e um assistente que responde perguntas com base em dados de banco de dados.",
                temperature=0.3,
                max_tokens=1000
            )

            return result.text

        except Exception as e:
            logger.warning(f"Failed to generate LLM summary: {e}")
            return self._generate_basic_summary(data, question)

    def _generate_basic_summary(
        self,
        data: List[Dict[str, Any]],
        question: str
    ) -> str:
        """Generate basic summary without LLM."""
        if not data:
            return "Nenhum resultado encontrado para sua consulta."

        if len(data) == 1:
            row = data[0]
            parts = []
            for col, value in row.items():
                if col not in ('id', 'uuid', 'deleted_at', 'is_deleted'):
                    formatted = self._format_value_for_display(value, col)
                    col_name = self._format_column_name(col)
                    parts.append(f"**{col_name}**: {formatted}")
            return " | ".join(parts)

        return f"Encontrados **{len(data)}** registros."

    def _generate_empty_response(self, question: str) -> str:
        """Generate response for empty results."""
        return (
            "Nao foram encontrados dados para sua consulta.\n\n"
            "Isso pode significar que:\n"
            "- Nao ha registros que correspondam aos criterios\n"
            "- O periodo especificado nao tem dados\n"
            "- Os filtros aplicados sao muito restritivos"
        )

    def _format_results_for_prompt(
        self,
        data: List[Dict[str, Any]],
        max_rows: int = 20
    ) -> str:
        """Format query results for LLM prompt."""
        if not data:
            return "Nenhum resultado"

        lines = []

        # Show header
        columns = list(data[0].keys())
        safe_columns = [c for c in columns if c not in ('id', 'uuid', 'deleted_at', 'is_deleted')]
        lines.append(" | ".join(safe_columns))
        lines.append("-" * 50)

        # Show rows (limited)
        for row in data[:max_rows]:
            values = []
            for col in safe_columns:
                val = row.get(col, '')
                formatted = self._format_value_for_display(val, col)
                values.append(str(formatted)[:30])  # Truncate long values
            lines.append(" | ".join(values))

        if len(data) > max_rows:
            lines.append(f"... e mais {len(data) - max_rows} registros")

        return "\n".join(lines)

    def _format_column_name(self, col: str) -> str:
        """Format column name for display."""
        # Common translations
        translations = {
            'value': 'Valor',
            'total': 'Total',
            'date': 'Data',
            'description': 'Descricao',
            'category': 'Categoria',
            'title': 'Titulo',
            'name': 'Nome',
            'status': 'Status',
            'payed': 'Pago',
            'received': 'Recebido',
            'pages': 'Paginas',
            'pages_read': 'Paginas Lidas',
            'reading_time': 'Tempo de Leitura',
            'reading_date': 'Data da Leitura',
            'read_status': 'Status de Leitura',
            'genre': 'Genero',
            'rating': 'Avaliacao',
            'current_balance': 'Saldo Atual',
            'account_name': 'Nome da Conta',
            'institution_name': 'Banco',
            'target_value': 'Meta',
            'current_value': 'Atual',
            'scheduled_date': 'Data Agendada',
            'task_name': 'Tarefa',
            'quantity_completed': 'Quantidade Concluida',
            'mes': 'Mes',
            'quantidade': 'Quantidade',
            'saldo_devedor': 'Saldo Devedor',
            'payed_value': 'Valor Pago',
        }

        return translations.get(col.lower(), col.replace('_', ' ').title())

    def _format_value_for_display(self, value: Any, col: str) -> str:
        """Format a value for display."""
        if value is None:
            return '-'

        # Monetary columns
        money_cols = ('value', 'total', 'current_balance', 'payed_value',
                      'saldo_devedor', 'default_value', 'credit_limit',
                      'target_value', 'monthly_income', 'tax_amount', 'net_amount')
        if col.lower() in money_cols or col.lower().endswith('_total'):
            if isinstance(value, (int, float, Decimal)):
                return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        # Boolean columns
        if isinstance(value, bool):
            return 'Sim' if value else 'Nao'

        # Date columns
        if col.lower() in ('date', 'reading_date', 'scheduled_date', 'start_date',
                           'end_date', 'due_date', 'payment_date', 'mes'):
            if hasattr(value, 'strftime'):
                return value.strftime('%d/%m/%Y')
            # Handle string dates
            if isinstance(value, str) and len(value) >= 10:
                try:
                    # ISO format YYYY-MM-DD
                    parts = value[:10].split('-')
                    if len(parts) == 3:
                        return f"{parts[2]}/{parts[1]}/{parts[0]}"
                except Exception:
                    pass

        # Time columns
        if col.lower() in ('reading_time',):
            if isinstance(value, (int, float)):
                hours = int(value) // 60
                mins = int(value) % 60
                if hours > 0:
                    return f"{hours}h {mins}min"
                return f"{mins}min"

        # Status columns
        status_translations = {
            'to_read': 'Para Ler',
            'reading': 'Lendo',
            'read': 'Lido',
            'pending': 'Pendente',
            'in_progress': 'Em Andamento',
            'completed': 'Concluido',
            'skipped': 'Pulado',
            'cancelled': 'Cancelado',
            'active': 'Ativo',
            'failed': 'Falhou',
            'paid': 'Pago',
            'overdue': 'Atrasado',
            'open': 'Aberta',
            'closed': 'Fechada',
        }
        if col.lower() in ('status', 'read_status') and isinstance(value, str):
            return status_translations.get(value.lower(), value)

        return str(value)

    def _is_numeric_column(self, data: List[Dict[str, Any]], col: str) -> bool:
        """Check if column contains numeric values."""
        if not data:
            return False
        sample = data[0].get(col)
        return isinstance(sample, (int, float, Decimal))

    def _get_chart_title(self, columns: List[str]) -> str:
        """Generate chart title from columns."""
        if 'value' in columns or 'total' in columns:
            return 'Evolucao de Valores'
        if 'pages_read' in columns:
            return 'Paginas Lidas'
        if 'reading_time' in columns:
            return 'Tempo de Leitura'
        return 'Grafico'


# Factory function
def get_query_result_formatter() -> QueryResultFormatter:
    """Get a configured QueryResultFormatter instance."""
    return QueryResultFormatter()
