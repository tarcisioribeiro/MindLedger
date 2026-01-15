"""
SQL Generator for AI Assistant.

Uses LLM to generate SQL queries from natural language questions.
"""

import logging
import re
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from .schema import SchemaService
from .prompts import get_sql_generation_prompt, detect_query_type, detect_module
from .validator import SQLValidator, SQLValidationError


logger = logging.getLogger(__name__)


class SQLGenerationError(Exception):
    """Exception raised when SQL generation fails."""

    def __init__(self, message: str, error_type: str = 'generation_error'):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)


@dataclass
class SQLGenerationResult:
    """Result of SQL generation."""
    sql: str
    query_type: str
    module: str
    tables_detected: List[str]
    explanation: Optional[str] = None
    confidence: float = 0.8
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SQLGenerator:
    """
    Generates SQL queries from natural language using LLM.

    Uses Groq LLM with comprehensive schema documentation to
    generate accurate PostgreSQL queries.
    """

    def __init__(
        self,
        schema_service: Optional[SchemaService] = None,
        validator: Optional[SQLValidator] = None
    ):
        """
        Initialize the SQL generator.

        Args:
            schema_service: Schema service for database structure
            validator: SQL validator for quick validation
        """
        self.schema = schema_service or SchemaService()
        self.validator = validator or SQLValidator(self.schema)
        self._llm_provider = None

    def _get_llm_provider(self):
        """Lazy-load the LLM provider."""
        if self._llm_provider is None:
            from ..llm_router.providers.groq import GroqProvider
            self._llm_provider = GroqProvider()
        return self._llm_provider

    def generate(
        self,
        question: str,
        owner_id: int,
        temperature: float = 0.1,
        max_tokens: int = 500
    ) -> SQLGenerationResult:
        """
        Generate SQL from natural language question.

        Args:
            question: User's question in natural language
            owner_id: Owner ID for context
            temperature: LLM temperature (low for deterministic SQL)
            max_tokens: Maximum tokens for SQL generation

        Returns:
            SQLGenerationResult with generated SQL

        Raises:
            SQLGenerationError: If generation fails
        """
        # Detect query type and module
        query_type = detect_query_type(question)
        module = detect_module(question)

        logger.info(
            f"Generating SQL for question: '{question[:50]}...' "
            f"[type={query_type}, module={module}]"
        )

        try:
            # Get schema prompt
            schema_text = self.schema.get_schema_for_prompt()

            # Build system prompt
            system_prompt = get_sql_generation_prompt(schema_text)

            # Build user prompt
            user_prompt = self._build_user_prompt(question, query_type, module)

            # Generate SQL using LLM
            provider = self._get_llm_provider()
            result = provider.generate(
                prompt=user_prompt,
                system=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Extract SQL from response
            sql = self._extract_sql(result.text)

            if not sql:
                raise SQLGenerationError(
                    "LLM did not generate valid SQL",
                    error_type='no_sql_generated'
                )

            # Quick validation
            is_valid, error = self.validator.quick_validate(sql)
            if not is_valid:
                raise SQLGenerationError(
                    f"Generated SQL is invalid: {error}",
                    error_type='invalid_sql'
                )

            # Detect tables used
            tables_detected = self._extract_tables_from_sql(sql)

            logger.info(f"SQL generated successfully: {sql[:100]}...")

            return SQLGenerationResult(
                sql=sql,
                query_type=query_type,
                module=module,
                tables_detected=tables_detected,
                explanation=self._generate_explanation(question, sql),
                confidence=self._estimate_confidence(sql, question),
                metadata={
                    'tokens_used': result.tokens_used,
                    'model': result.model,
                }
            )

        except SQLGenerationError:
            raise
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            raise SQLGenerationError(
                f"Failed to generate SQL: {str(e)}",
                error_type='llm_error'
            )

    def generate_with_fallback(
        self,
        question: str,
        owner_id: int,
        max_retries: int = 2
    ) -> SQLGenerationResult:
        """
        Generate SQL with retry on failure.

        Args:
            question: User's question
            owner_id: Owner ID
            max_retries: Maximum retry attempts

        Returns:
            SQLGenerationResult on success

        Raises:
            SQLGenerationError: If all attempts fail
        """
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                # Increase temperature slightly on retries for variety
                temperature = 0.1 + (attempt * 0.1)
                return self.generate(question, owner_id, temperature=temperature)
            except SQLGenerationError as e:
                last_error = e
                logger.warning(
                    f"SQL generation attempt {attempt + 1} failed: {e.message}"
                )

        raise last_error

    def _build_user_prompt(
        self,
        question: str,
        query_type: str,
        module: str
    ) -> str:
        """Build the user prompt for SQL generation."""
        prompt_parts = [
            f"Pergunta do usuario: {question}",
            "",
            f"Tipo de query detectado: {query_type}",
            f"Modulo detectado: {module}",
            "",
            "Gere APENAS o SQL, sem explicacoes. O SQL deve estar pronto para execucao.",
        ]

        # Add hints based on query type
        if query_type == 'aggregation':
            prompt_parts.append("Use funcoes de agregacao (SUM, COUNT, AVG) conforme apropriado.")
        elif query_type == 'trend':
            prompt_parts.append("Use DATE_TRUNC para agrupar por periodo e ORDER BY para ordenar cronologicamente.")
        elif query_type == 'listing':
            prompt_parts.append("Retorne colunas relevantes e ordene de forma logica.")

        return "\n".join(prompt_parts)

    def _extract_sql(self, llm_response: str) -> Optional[str]:
        """
        Extract SQL query from LLM response.

        Handles various formats:
        - Plain SQL
        - SQL in markdown code blocks
        - SQL with explanations before/after
        """
        # Try to extract from code block first
        code_block_match = re.search(
            r'```(?:sql)?\s*(SELECT.*?)```',
            llm_response,
            re.IGNORECASE | re.DOTALL
        )
        if code_block_match:
            return code_block_match.group(1).strip()

        # Try to find SELECT statement directly
        select_match = re.search(
            r'(SELECT\s+.+?)(?:;|\n\n|$)',
            llm_response,
            re.IGNORECASE | re.DOTALL
        )
        if select_match:
            sql = select_match.group(1).strip()
            # Clean up trailing text that's not SQL
            sql = re.sub(r'\n[^A-Z\s].*$', '', sql, flags=re.DOTALL)
            return sql

        # Try WITH (CTE) pattern
        with_match = re.search(
            r'(WITH\s+.+?SELECT.+?)(?:;|\n\n|$)',
            llm_response,
            re.IGNORECASE | re.DOTALL
        )
        if with_match:
            return with_match.group(1).strip()

        return None

    def _extract_tables_from_sql(self, sql: str) -> List[str]:
        """Extract table names from SQL."""
        tables = []

        # FROM clause
        from_matches = re.findall(r'\bFROM\s+(\w+)', sql, re.IGNORECASE)
        tables.extend(from_matches)

        # JOIN clauses
        join_matches = re.findall(r'\bJOIN\s+(\w+)', sql, re.IGNORECASE)
        tables.extend(join_matches)

        # Filter to known tables
        known_tables = set(self.schema.get_all_tables())
        return [t.lower() for t in tables if t.lower() in known_tables]

    def _generate_explanation(self, question: str, sql: str) -> str:
        """Generate a brief explanation of what the SQL does."""
        # Simple rule-based explanation
        explanation_parts = []

        if 'SUM(' in sql.upper():
            explanation_parts.append("soma valores")
        if 'COUNT(' in sql.upper():
            explanation_parts.append("conta registros")
        if 'AVG(' in sql.upper():
            explanation_parts.append("calcula media")
        if 'GROUP BY' in sql.upper():
            explanation_parts.append("agrupa resultados")
        if 'ORDER BY' in sql.upper():
            if 'DESC' in sql.upper():
                explanation_parts.append("ordena do maior para menor")
            else:
                explanation_parts.append("ordena resultados")
        if 'DATE_TRUNC' in sql.upper():
            explanation_parts.append("agrupa por periodo")

        tables = self._extract_tables_from_sql(sql)
        if tables:
            table_names = {
                'expenses_expense': 'despesas',
                'revenues_revenue': 'receitas',
                'library_book': 'livros',
                'library_reading': 'leituras',
                'accounts_account': 'contas',
                'personal_planning_goal': 'metas',
                'personal_planning_taskinstance': 'tarefas',
                'security_password': 'senhas',
            }
            readable_tables = [table_names.get(t, t) for t in tables]
            explanation_parts.append(f"consulta {', '.join(readable_tables)}")

        if explanation_parts:
            return "Esta query " + ", ".join(explanation_parts) + "."
        return "Query gerada para responder a pergunta."

    def _estimate_confidence(self, sql: str, question: str) -> float:
        """
        Estimate confidence in the generated SQL.

        Based on:
        - SQL structure completeness
        - Question clarity
        - Table detection
        """
        confidence = 0.7  # Base confidence

        # Bonus for well-structured SQL
        if 'SELECT' in sql.upper() and 'FROM' in sql.upper():
            confidence += 0.1
        if 'WHERE' in sql.upper():
            confidence += 0.05
        if 'deleted_at IS NULL' in sql.lower() or 'is_deleted' in sql.lower():
            confidence += 0.05

        # Bonus for clear question
        clear_keywords = ['quanto', 'quantos', 'quais', 'liste', 'mostre', 'total']
        if any(kw in question.lower() for kw in clear_keywords):
            confidence += 0.05

        # Cap at 0.95
        return min(0.95, confidence)


# Factory function
def get_sql_generator() -> SQLGenerator:
    """Get a configured SQLGenerator instance."""
    return SQLGenerator()
