"""
SQL Query Executor for AI Assistant.

Safely executes validated SQL queries with timeout and result limiting.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import date, datetime, time as time_type
import uuid

from django.db import connection, OperationalError


logger = logging.getLogger(__name__)


class QueryExecutionError(Exception):
    """Exception raised when query execution fails."""

    def __init__(self, message: str, error_type: str = 'execution_error'):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)


class QueryTimeoutError(QueryExecutionError):
    """Exception raised when query times out."""

    def __init__(self, message: str = "Query execution timed out"):
        super().__init__(message, error_type='timeout')


@dataclass
class QueryResult:
    """Result of a query execution."""
    columns: List[str]
    rows: List[Tuple[Any, ...]]
    row_count: int
    execution_time_ms: float
    sql: str
    truncated: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Convert rows to list of dictionaries."""
        return [
            dict(zip(self.columns, row))
            for row in self.rows
        ]

    def to_formatted_rows(self) -> List[Dict[str, str]]:
        """Convert rows to list of dictionaries with formatted values."""
        result = []
        for row in self.rows:
            formatted_row = {}
            for col, val in zip(self.columns, row):
                formatted_row[col] = self._format_value(val)
            result.append(formatted_row)
        return result

    @staticmethod
    def _format_value(value: Any) -> str:
        """Format a value for display."""
        if value is None:
            return '-'
        if isinstance(value, Decimal):
            return f"{value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        if isinstance(value, float):
            return f"{value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        if isinstance(value, date):
            return value.strftime('%d/%m/%Y')
        if isinstance(value, datetime):
            return value.strftime('%d/%m/%Y %H:%M')
        if isinstance(value, time_type):
            return value.strftime('%H:%M')
        if isinstance(value, uuid.UUID):
            return str(value)
        if isinstance(value, bool):
            return 'Sim' if value else 'Nao'
        return str(value)


class QueryExecutor:
    """
    Safely executes validated SQL queries.

    Features:
    - Query timeout protection
    - Result limiting
    - Execution time tracking
    - Value serialization for JSON
    """

    # Default timeout in seconds
    DEFAULT_TIMEOUT = 10

    # Default maximum rows
    DEFAULT_MAX_ROWS = 500

    def __init__(
        self,
        timeout_seconds: int = DEFAULT_TIMEOUT,
        max_rows: int = DEFAULT_MAX_ROWS
    ):
        """
        Initialize the query executor.

        Args:
            timeout_seconds: Maximum query execution time
            max_rows: Maximum number of rows to return
        """
        self.timeout = timeout_seconds
        self.max_rows = max_rows

    def execute(self, sql: str) -> QueryResult:
        """
        Execute a SQL query safely.

        Args:
            sql: The validated SQL query to execute

        Returns:
            QueryResult with data and metadata

        Raises:
            QueryExecutionError: If execution fails
            QueryTimeoutError: If query times out
        """
        start_time = time.time()

        try:
            with connection.cursor() as cursor:
                # Set statement timeout
                cursor.execute(f"SET statement_timeout = '{self.timeout}s'")

                try:
                    # Execute the query
                    cursor.execute(sql)

                    # Get column names
                    columns = [col[0] for col in cursor.description] if cursor.description else []

                    # Fetch rows with limit
                    rows = cursor.fetchmany(self.max_rows + 1)

                    # Check if there are more rows
                    truncated = len(rows) > self.max_rows
                    if truncated:
                        rows = rows[:self.max_rows]

                    # Serialize values
                    serialized_rows = [
                        tuple(self._serialize_value(v) for v in row)
                        for row in rows
                    ]

                    execution_time = (time.time() - start_time) * 1000

                    logger.info(
                        f"Query executed successfully in {execution_time:.2f}ms, "
                        f"{len(serialized_rows)} rows returned"
                    )

                    return QueryResult(
                        columns=columns,
                        rows=serialized_rows,
                        row_count=len(serialized_rows),
                        execution_time_ms=execution_time,
                        sql=sql,
                        truncated=truncated,
                        metadata={
                            'timeout_seconds': self.timeout,
                            'max_rows': self.max_rows,
                        }
                    )

                finally:
                    # Reset timeout
                    cursor.execute("RESET statement_timeout")

        except OperationalError as e:
            error_msg = str(e)

            # Check for timeout
            if 'canceling statement due to statement timeout' in error_msg:
                logger.warning(f"Query timed out after {self.timeout}s")
                raise QueryTimeoutError(
                    f"Query exceeded {self.timeout} second timeout"
                )

            logger.error(f"Query execution failed: {error_msg}")
            raise QueryExecutionError(
                f"Query execution failed: {error_msg}",
                error_type='database_error'
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Unexpected error during query execution: {error_msg}")
            raise QueryExecutionError(
                f"Unexpected error: {error_msg}",
                error_type='unexpected_error'
            )

    def execute_with_retry(
        self,
        sql: str,
        max_retries: int = 2,
        retry_delay: float = 0.5
    ) -> QueryResult:
        """
        Execute query with retry on transient failures.

        Args:
            sql: The SQL query to execute
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds

        Returns:
            QueryResult on success

        Raises:
            QueryExecutionError: If all retries fail
        """
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                return self.execute(sql)
            except QueryTimeoutError:
                # Don't retry timeouts
                raise
            except QueryExecutionError as e:
                last_error = e
                if attempt < max_retries:
                    logger.warning(
                        f"Query failed (attempt {attempt + 1}/{max_retries + 1}), "
                        f"retrying in {retry_delay}s: {e.message}"
                    )
                    time.sleep(retry_delay)

        raise last_error

    def _serialize_value(self, value: Any) -> Any:
        """
        Serialize a database value for JSON compatibility.

        Args:
            value: The value to serialize

        Returns:
            JSON-serializable value
        """
        if value is None:
            return None

        if isinstance(value, Decimal):
            return float(value)

        if isinstance(value, datetime):
            return value.isoformat()

        if isinstance(value, date):
            return value.isoformat()

        if isinstance(value, time_type):
            return value.isoformat()

        if isinstance(value, uuid.UUID):
            return str(value)

        if isinstance(value, bytes):
            return value.decode('utf-8', errors='replace')

        if isinstance(value, (list, dict)):
            return value

        return value

    def get_row_estimate(self, sql: str) -> Optional[int]:
        """
        Get an estimate of rows that would be returned.

        Uses EXPLAIN to get row estimate without executing the full query.

        Args:
            sql: The SQL query to estimate

        Returns:
            Estimated row count or None if estimation fails
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"EXPLAIN (FORMAT JSON) {sql}")
                result = cursor.fetchone()

                if result and result[0]:
                    plan = result[0][0]
                    return plan.get('Plan', {}).get('Plan Rows', 0)

        except Exception as e:
            logger.warning(f"Failed to estimate rows: {e}")

        return None


class BatchQueryExecutor:
    """
    Executor for multiple queries in a single transaction.
    """

    def __init__(self, executor: Optional[QueryExecutor] = None):
        """
        Initialize batch executor.

        Args:
            executor: QueryExecutor instance to use
        """
        self.executor = executor or QueryExecutor()

    def execute_batch(
        self,
        queries: List[str],
        stop_on_error: bool = True
    ) -> List[QueryResult]:
        """
        Execute multiple queries.

        Args:
            queries: List of SQL queries to execute
            stop_on_error: Whether to stop on first error

        Returns:
            List of QueryResults
        """
        results = []

        for sql in queries:
            try:
                result = self.executor.execute(sql)
                results.append(result)
            except QueryExecutionError as e:
                if stop_on_error:
                    raise
                results.append(QueryResult(
                    columns=[],
                    rows=[],
                    row_count=0,
                    execution_time_ms=0,
                    sql=sql,
                    error=e.message
                ))

        return results


# Factory function
def get_query_executor(
    timeout_seconds: int = QueryExecutor.DEFAULT_TIMEOUT,
    max_rows: int = QueryExecutor.DEFAULT_MAX_ROWS
) -> QueryExecutor:
    """
    Get a configured QueryExecutor instance.

    Args:
        timeout_seconds: Query timeout in seconds
        max_rows: Maximum rows to return

    Returns:
        Configured QueryExecutor
    """
    return QueryExecutor(
        timeout_seconds=timeout_seconds,
        max_rows=max_rows
    )
