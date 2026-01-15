"""
SQL Validator for AI Assistant.

Validates and sanitizes generated SQL queries for safe execution.
"""

import re
import logging
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple

from .schema import SchemaService, SENSITIVE_FIELDS, MODELS_SCHEMA


logger = logging.getLogger(__name__)


class SQLValidationError(Exception):
    """Exception raised when SQL validation fails."""

    def __init__(self, message: str, error_type: str = 'validation_error'):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)


@dataclass
class ValidationResult:
    """Result of SQL validation."""
    is_valid: bool
    sanitized_sql: str
    tables_used: List[str]
    columns_used: List[str]
    has_aggregation: bool
    has_grouping: bool
    warnings: List[str]
    error: Optional[str] = None


class SQLValidator:
    """
    Validates and sanitizes generated SQL for safe execution.

    Security measures:
    1. Only SELECT statements allowed
    2. Forbidden keywords/patterns blocked
    3. Table whitelist enforcement
    4. Sensitive columns filtered
    5. Owner filter injection
    6. Limit injection if missing
    """

    # Allowed SQL keywords for SELECT queries
    ALLOWED_KEYWORDS = {
        'SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER',
        'FULL', 'CROSS', 'ON', 'AND', 'OR', 'NOT', 'IN', 'BETWEEN', 'LIKE',
        'ILIKE', 'IS', 'NULL', 'TRUE', 'FALSE', 'AS', 'DISTINCT', 'ALL',
        'GROUP', 'BY', 'HAVING', 'ORDER', 'ASC', 'DESC', 'NULLS', 'FIRST',
        'LAST', 'LIMIT', 'OFFSET', 'UNION', 'INTERSECT', 'EXCEPT',
        'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'CAST', 'COALESCE', 'NULLIF',
        'EXISTS', 'ANY', 'SOME',
        # Aggregate functions
        'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'ARRAY_AGG', 'STRING_AGG',
        # Date functions
        'DATE_TRUNC', 'DATE_PART', 'EXTRACT', 'CURRENT_DATE', 'CURRENT_TIME',
        'CURRENT_TIMESTAMP', 'NOW', 'INTERVAL', 'YEAR', 'MONTH', 'DAY',
        'HOUR', 'MINUTE', 'SECOND', 'WEEK', 'QUARTER',
        # String functions
        'LOWER', 'UPPER', 'TRIM', 'LTRIM', 'RTRIM', 'LENGTH', 'SUBSTRING',
        'CONCAT', 'REPLACE', 'POSITION', 'SPLIT_PART',
        # Numeric functions
        'ROUND', 'FLOOR', 'CEIL', 'ABS', 'MOD',
        # Type casting
        'INTEGER', 'BIGINT', 'DECIMAL', 'NUMERIC', 'VARCHAR', 'TEXT',
        'DATE', 'TIME', 'TIMESTAMP', 'BOOLEAN', 'JSONB', 'JSON',
    }

    # Forbidden patterns that indicate dangerous operations
    FORBIDDEN_PATTERNS = [
        # DML/DDL operations
        (r'\b(INSERT)\s+INTO\b', 'INSERT not allowed'),
        (r'\b(UPDATE)\s+\w+\s+SET\b', 'UPDATE not allowed'),
        (r'\b(DELETE)\s+FROM\b', 'DELETE not allowed'),
        (r'\b(DROP)\s+(TABLE|DATABASE|INDEX|VIEW|SCHEMA)\b', 'DROP not allowed'),
        (r'\b(CREATE)\s+(TABLE|DATABASE|INDEX|VIEW|SCHEMA)\b', 'CREATE not allowed'),
        (r'\b(ALTER)\s+(TABLE|DATABASE)\b', 'ALTER not allowed'),
        (r'\b(TRUNCATE)\s+TABLE\b', 'TRUNCATE not allowed'),

        # Permission operations
        (r'\b(GRANT|REVOKE)\b', 'Permission operations not allowed'),

        # Execution
        (r'\b(EXECUTE|EXEC)\b', 'EXECUTE not allowed'),

        # Multiple statements
        (r';\s*\S', 'Multiple statements not allowed'),

        # Comments (could hide malicious code)
        (r'--', 'SQL comments not allowed'),
        (r'/\*', 'Block comments not allowed'),

        # System operations
        (r'\bpg_', 'System table access not allowed'),
        (r'\binformation_schema\b', 'Information schema access not allowed'),

        # File operations
        (r'\bCOPY\b', 'COPY not allowed'),
        (r'\bLOAD\b', 'LOAD not allowed'),

        # Extensions
        (r'\bCREATE\s+EXTENSION\b', 'Extension creation not allowed'),
    ]

    # Maximum result limit
    DEFAULT_MAX_LIMIT = 500
    MAX_ALLOWED_LIMIT = 1000

    def __init__(self, schema_service: Optional[SchemaService] = None):
        """
        Initialize the SQL validator.

        Args:
            schema_service: Optional SchemaService instance
        """
        self.schema = schema_service or SchemaService()
        self.allowed_tables = set(MODELS_SCHEMA.keys())

    def validate(
        self,
        sql: str,
        owner_id: int,
        inject_owner_filter: bool = True,
        inject_limit: bool = True,
        max_limit: int = DEFAULT_MAX_LIMIT
    ) -> ValidationResult:
        """
        Validate and sanitize SQL query.

        Args:
            sql: The SQL query to validate
            owner_id: Owner ID for filtering
            inject_owner_filter: Whether to inject owner filter
            inject_limit: Whether to inject LIMIT if missing
            max_limit: Maximum limit to enforce

        Returns:
            ValidationResult with sanitized SQL or error

        Raises:
            SQLValidationError: If validation fails with unrecoverable error
        """
        warnings = []

        # Step 1: Basic cleanup
        sql = self._clean_sql(sql)

        # Step 2: Check if it's a SELECT statement
        if not self._is_select_statement(sql):
            raise SQLValidationError(
                "Only SELECT statements are allowed",
                error_type='forbidden_operation'
            )

        # Step 3: Check for forbidden patterns
        forbidden = self._check_forbidden_patterns(sql)
        if forbidden:
            raise SQLValidationError(
                f"Forbidden pattern detected: {forbidden}",
                error_type='forbidden_pattern'
            )

        # Step 4: Extract and validate tables
        tables_used = self._extract_tables(sql)
        invalid_tables = [t for t in tables_used if t not in self.allowed_tables]
        if invalid_tables:
            raise SQLValidationError(
                f"Access to tables not allowed: {', '.join(invalid_tables)}",
                error_type='invalid_table'
            )

        # Step 5: Check for sensitive columns
        sensitive_cols = self._check_sensitive_columns(sql)
        if sensitive_cols:
            # Instead of failing, we'll warn and try to remove them
            warnings.append(f"Sensitive columns detected and removed: {', '.join(sensitive_cols)}")
            sql = self._remove_sensitive_columns(sql, sensitive_cols)

        # Step 6: Extract columns used
        columns_used = self._extract_columns(sql)

        # Step 7: Check for aggregation and grouping
        has_aggregation = self._has_aggregation(sql)
        has_grouping = self._has_grouping(sql)

        # Step 8: Inject owner filter if needed
        if inject_owner_filter:
            sql = self._inject_owner_filter(sql, owner_id, tables_used)

        # Step 9: Ensure soft delete filter
        sql = self._ensure_soft_delete_filter(sql, tables_used)

        # Step 10: Inject or adjust LIMIT
        if inject_limit:
            sql = self._inject_or_adjust_limit(sql, max_limit)

        return ValidationResult(
            is_valid=True,
            sanitized_sql=sql.strip(),
            tables_used=tables_used,
            columns_used=columns_used,
            has_aggregation=has_aggregation,
            has_grouping=has_grouping,
            warnings=warnings
        )

    def _clean_sql(self, sql: str) -> str:
        """Clean and normalize SQL query."""
        # Remove leading/trailing whitespace
        sql = sql.strip()

        # Remove markdown code blocks if present
        sql = re.sub(r'^```sql\s*', '', sql)
        sql = re.sub(r'\s*```$', '', sql)
        sql = re.sub(r'^```\s*', '', sql)

        # Normalize whitespace
        sql = ' '.join(sql.split())

        # Remove trailing semicolon (we'll add it back if needed)
        sql = sql.rstrip(';')

        return sql

    def _is_select_statement(self, sql: str) -> bool:
        """Check if SQL is a SELECT statement."""
        sql_upper = sql.upper().strip()
        # Allow WITH (CTE) followed by SELECT
        return sql_upper.startswith('SELECT') or sql_upper.startswith('WITH')

    def _check_forbidden_patterns(self, sql: str) -> Optional[str]:
        """Check for forbidden patterns in SQL."""
        for pattern, message in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                return message
        return None

    def _extract_tables(self, sql: str) -> List[str]:
        """Extract table names from SQL query."""
        tables = []

        # Pattern to match table names after FROM and JOIN
        patterns = [
            r'\bFROM\s+(\w+)',
            r'\bJOIN\s+(\w+)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            tables.extend(matches)

        # Filter to only known tables
        return [t.lower() for t in tables if t.lower() in self.allowed_tables]

    def _extract_columns(self, sql: str) -> List[str]:
        """Extract column names from SQL query."""
        columns = []

        # Simple extraction - get words that look like column references
        # This is not perfect but good enough for logging
        select_match = re.search(r'SELECT\s+(.+?)\s+FROM', sql, re.IGNORECASE | re.DOTALL)
        if select_match:
            select_clause = select_match.group(1)
            # Extract column names (simple patterns)
            col_patterns = re.findall(r'\b(\w+)\s*(?:,|AS|$)', select_clause, re.IGNORECASE)
            columns.extend(col_patterns)

        return [c.lower() for c in columns if c.upper() not in self.ALLOWED_KEYWORDS]

    def _check_sensitive_columns(self, sql: str) -> List[str]:
        """Check if SQL references sensitive columns."""
        found = []
        for field in SENSITIVE_FIELDS:
            if re.search(rf'\b{re.escape(field)}\b', sql, re.IGNORECASE):
                found.append(field)
        return found

    def _remove_sensitive_columns(self, sql: str, sensitive_cols: List[str]) -> str:
        """Remove sensitive columns from SELECT clause."""
        for col in sensitive_cols:
            # Remove column from SELECT list
            sql = re.sub(
                rf',?\s*\b{re.escape(col)}\b\s*,?',
                ',',
                sql,
                flags=re.IGNORECASE
            )
            # Clean up double commas
            sql = re.sub(r',\s*,', ',', sql)
            # Clean up leading/trailing commas in SELECT
            sql = re.sub(r'SELECT\s*,', 'SELECT ', sql, flags=re.IGNORECASE)
            sql = re.sub(r',\s*FROM', ' FROM', sql, flags=re.IGNORECASE)

        return sql

    def _has_aggregation(self, sql: str) -> bool:
        """Check if SQL has aggregation functions."""
        agg_funcs = ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'ARRAY_AGG', 'STRING_AGG']
        pattern = r'\b(' + '|'.join(agg_funcs) + r')\s*\('
        return bool(re.search(pattern, sql, re.IGNORECASE))

    def _has_grouping(self, sql: str) -> bool:
        """Check if SQL has GROUP BY clause."""
        return bool(re.search(r'\bGROUP\s+BY\b', sql, re.IGNORECASE))

    def _inject_owner_filter(
        self,
        sql: str,
        owner_id: int,
        tables_used: List[str]
    ) -> str:
        """Inject owner filter into WHERE clause."""
        owner_conditions = []

        for table in tables_used:
            table_schema = self.schema.get_table_schema(table)
            if not table_schema:
                continue

            owner_field = table_schema.get('owner_field')
            if not owner_field:
                continue

            # Get table alias if used
            alias_match = re.search(
                rf'\b{table}\s+(?:AS\s+)?(\w+)\b',
                sql,
                re.IGNORECASE
            )
            prefix = alias_match.group(1) if alias_match else table

            owner_conditions.append(f"{prefix}.{owner_field} = {owner_id}")

        if not owner_conditions:
            return sql

        # Check if WHERE exists
        where_match = re.search(r'\bWHERE\b', sql, re.IGNORECASE)

        if where_match:
            # Insert after WHERE
            where_pos = where_match.end()
            condition = ' (' + ' OR '.join(owner_conditions) + ') AND'
            sql = sql[:where_pos] + condition + sql[where_pos:]
        else:
            # Find position to insert WHERE (before GROUP BY, ORDER BY, or LIMIT)
            insert_patterns = [
                r'\bGROUP\s+BY\b',
                r'\bORDER\s+BY\b',
                r'\bLIMIT\b',
                r'$'
            ]

            insert_pos = len(sql)
            for pattern in insert_patterns:
                match = re.search(pattern, sql, re.IGNORECASE)
                if match:
                    insert_pos = match.start()
                    break

            condition = ' WHERE (' + ' OR '.join(owner_conditions) + ') '
            sql = sql[:insert_pos] + condition + sql[insert_pos:]

        return sql

    def _ensure_soft_delete_filter(self, sql: str, tables_used: List[str]) -> str:
        """Ensure soft delete filter is present for tables that use it."""
        for table in tables_used:
            table_schema = self.schema.get_table_schema(table)
            if not table_schema or not table_schema.get('soft_delete'):
                continue

            # Check if deleted_at filter already exists
            if re.search(r'\bdeleted_at\s+IS\s+NULL\b', sql, re.IGNORECASE):
                continue
            if re.search(r'\bis_deleted\s*=\s*false\b', sql, re.IGNORECASE):
                continue

            # Get table alias if used
            alias_match = re.search(
                rf'\b{table}\s+(?:AS\s+)?(\w+)\b',
                sql,
                re.IGNORECASE
            )
            prefix = alias_match.group(1) if alias_match else table

            # Add deleted_at IS NULL condition
            where_match = re.search(r'\bWHERE\b', sql, re.IGNORECASE)
            if where_match:
                # Find end of WHERE clause conditions
                where_pos = where_match.end()
                sql = sql[:where_pos] + f" {prefix}.deleted_at IS NULL AND" + sql[where_pos:]
            else:
                # Insert WHERE before GROUP BY, ORDER BY, LIMIT, or at end
                insert_patterns = [
                    r'\bGROUP\s+BY\b',
                    r'\bORDER\s+BY\b',
                    r'\bLIMIT\b',
                ]
                insert_pos = len(sql)
                for pattern in insert_patterns:
                    match = re.search(pattern, sql, re.IGNORECASE)
                    if match:
                        insert_pos = match.start()
                        break

                sql = sql[:insert_pos] + f" WHERE {prefix}.deleted_at IS NULL " + sql[insert_pos:]

        return sql

    def _inject_or_adjust_limit(self, sql: str, max_limit: int) -> str:
        """Inject LIMIT if missing or adjust if too high."""
        limit_match = re.search(r'\bLIMIT\s+(\d+)\b', sql, re.IGNORECASE)

        if limit_match:
            current_limit = int(limit_match.group(1))
            if current_limit > self.MAX_ALLOWED_LIMIT:
                # Reduce to max allowed
                sql = re.sub(
                    r'\bLIMIT\s+\d+\b',
                    f'LIMIT {max_limit}',
                    sql,
                    flags=re.IGNORECASE
                )
        else:
            # Add LIMIT at the end
            sql = sql.rstrip() + f' LIMIT {max_limit}'

        return sql

    def quick_validate(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        Quick validation without full analysis.

        Returns:
            Tuple of (is_valid, error_message)
        """
        sql = self._clean_sql(sql)

        if not self._is_select_statement(sql):
            return False, "Only SELECT statements are allowed"

        forbidden = self._check_forbidden_patterns(sql)
        if forbidden:
            return False, f"Forbidden pattern: {forbidden}"

        return True, None
