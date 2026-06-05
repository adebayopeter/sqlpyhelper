"""
sqlpyhelper.async_helper
~~~~~~~~~~~~~~~~~~~~~~~~
Async-native database helper supporting SQLite, PostgreSQL, MySQL,
SQL Server, and Oracle.

Uses async-native drivers:
- SQLite:     aiosqlite
- PostgreSQL: asyncpg
- MySQL:      aiomysql
- SQL Server: aioodbc
- Oracle:     python-oracledb (async mode)

Example usage::

    import asyncio
    from sqlpyhelper.async_helper import AsyncSQLPyHelper

    async def main():
        async with AsyncSQLPyHelper(db_type="sqlite", database="my.db") as db:
            await db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER, name TEXT)")
            await db.execute("INSERT INTO users VALUES ($1, $2)", 1, "Alice")
            rows = await db.fetch_all("SELECT * FROM users")
            print(rows)

    asyncio.run(main())
"""

import logging
import os
from typing import Any, Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("sqlpyhelper.async")


class AsyncConnectionError(Exception):
    """Raised when an async database connection fails."""


class AsyncQueryError(Exception):
    """Raised when an async query fails."""


class AsyncSQLPyHelper:
    """
    Async-native database helper with a unified API across
    SQLite, PostgreSQL, MySQL, SQL Server, and Oracle.

    Use as an async context manager::

        async with AsyncSQLPyHelper(db_type="postgres", ...) as db:
            rows = await db.fetch_all("SELECT * FROM users")

    Or manage the connection lifecycle manually::

        db = AsyncSQLPyHelper(db_type="sqlite", database="my.db")
        await db.connect()
        try:
            rows = await db.fetch_all("SELECT * FROM users")
        finally:
            await db.close()
    """

    def __init__(
        self,
        db_type: Optional[str] = None,
        host: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        driver: Optional[str] = None,
        port: Optional[str] = None,
        oracle_sid: Optional[str] = None,
    ) -> None:
        self.db_type: str = (db_type or os.getenv("DB_TYPE") or "").lower()
        self.host: Optional[str] = host or os.getenv("DB_HOST")
        self.user: Optional[str] = user or os.getenv("DB_USER")
        self.password: Optional[str] = password or os.getenv("DB_PASSWORD")
        self.database: Optional[str] = database or os.getenv("DB_NAME")
        self.driver: Optional[str] = driver or os.getenv("DB_DRIVER")
        self.port: Optional[str] = port or os.getenv("DB_PORT")
        self.oracle_sid: Optional[str] = oracle_sid or os.getenv("ORACLE_SID")

        self._connection: Any = None
        self._pool: Any = None

        if not self.db_type or not self.database:
            raise ValueError("Missing required database configuration.")

        if self.db_type not in ("sqlite", "postgres", "mysql", "sqlserver", "oracle"):
            raise ValueError(f"Unsupported database type: {self.db_type!r}")

    # -----------------------------------------------------------------------
    # Connection lifecycle
    # -----------------------------------------------------------------------

    async def connect(self) -> None:
        """Open the database connection."""
        try:
            if self.db_type == "sqlite":
                import aiosqlite

                self._connection = await aiosqlite.connect(self.database or "")  # type: ignore[arg-type]
                self._connection.row_factory = aiosqlite.Row
                logger.info("Connected to SQLite database: %s", self.database)

            elif self.db_type == "postgres":
                import asyncpg

                self._connection = await asyncpg.connect(
                    host=self.host,
                    port=int(self.port or 5432),
                    user=self.user,
                    password=self.password,
                    database=self.database,
                )
                logger.info("Connected to PostgreSQL database: %s", self.database)

            elif self.db_type == "mysql":
                import aiomysql

                self._connection = await aiomysql.connect(
                    host=self.host or "localhost",
                    port=int(self.port or 3306),
                    user=self.user,
                    password=self.password or "",
                    db=self.database,
                    autocommit=False,
                )
                logger.info("Connected to MySQL database: %s", self.database)

            elif self.db_type == "sqlserver":
                import aioodbc

                dsn = (
                    f"DRIVER={self.driver};"
                    f"SERVER={self.host};"
                    f"DATABASE={self.database};"
                    f"UID={self.user};"
                    f"PWD={self.password}"
                )
                self._connection = await aioodbc.connect(dsn=dsn)
                logger.info("Connected to SQL Server database: %s", self.database)

            elif self.db_type == "oracle":
                import oracledb

                oracle_port = int(os.getenv("ORACLE_DB_PORT", "1521"))
                dsn = oracledb.makedsn(
                    self.host, oracle_port, sid=self.oracle_sid  # type: ignore[arg-type]
                )
                self._connection = await oracledb.connect_async(
                    user=self.user, password=self.password, dsn=dsn
                )
                logger.info("Connected to Oracle database: %s", self.oracle_sid)

        except Exception as e:
            raise AsyncConnectionError(
                f"Failed to connect to {self.db_type}: {e}"
            ) from e

    async def close(self) -> None:
        """Close the database connection."""
        try:
            if self._connection is not None:
                await self._connection.close()
                self._connection = None
                logger.info("Closed %s connection", self.db_type)
        except Exception as e:
            raise AsyncConnectionError(f"Failed to close connection: {e}") from e

    async def __aenter__(self) -> "AsyncSQLPyHelper":
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        await self.close()
        return False

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _check_connection(self) -> None:
        if self._connection is None:
            raise AsyncConnectionError(
                "No active connection. Call connect() or use async with."
            )

    def _adapt_query(self, query: str, args: tuple) -> tuple[str, tuple]:
        """
        Adapt a query and its arguments for the active database driver.

        asyncpg uses $1, $2, ... positional placeholders.
        aiosqlite and aiomysql use ? and %s respectively.
        Callers should write queries using $1, $2, ... style and this
        method will translate as needed.
        """
        if not args:
            return query, args

        if self.db_type == "postgres":
            # asyncpg natively uses $1, $2 — pass through unchanged
            return query, args

        elif self.db_type == "sqlite":
            # Replace $1, $2 with ?
            import re

            adapted = re.sub(r"\$\d+", "?", query)
            return adapted, args

        elif self.db_type in ("mysql", "sqlserver"):
            # Replace $1, $2 with %s
            import re

            adapted = re.sub(r"\$\d+", "%s", query)
            return adapted, args

        elif self.db_type == "oracle":
            # Replace $1, $2 with :1, :2
            import re

            def replace_placeholder(m: Any) -> str:
                return f":{m.group(0)[1:]}"

            adapted = re.sub(r"\$(\d+)", replace_placeholder, query)
            return adapted, args

        return query, args

    # -----------------------------------------------------------------------
    # Query execution
    # -----------------------------------------------------------------------

    async def execute(self, query: str, *args: Any) -> None:
        """
        Execute a SQL statement (INSERT, UPDATE, DELETE, DDL).

        Use $1, $2, ... for parameterised values::

            await db.execute(
                "INSERT INTO users (id, name) VALUES ($1, $2)",
                1, "Alice"
            )

        Args:
            query: SQL query string using $1, $2 placeholders.
            *args: Query parameters.

        Raises:
            AsyncQueryError: If the query fails.
        """
        self._check_connection()
        adapted_query, adapted_args = self._adapt_query(query, args)
        try:
            if self.db_type == "postgres":
                await self._connection.execute(adapted_query, *adapted_args)

            elif self.db_type == "sqlite":
                await self._connection.execute(adapted_query, adapted_args)
                await self._connection.commit()

            elif self.db_type in ("mysql", "sqlserver"):
                async with self._connection.cursor() as cursor:
                    await cursor.execute(adapted_query, adapted_args)
                await self._connection.commit()

            elif self.db_type == "oracle":
                cursor = self._connection.cursor()
                await cursor.execute(adapted_query, adapted_args)
                await self._connection.commit()

            logger.debug("Executed: %s", query)

        except Exception as e:
            raise AsyncQueryError(f"Query failed: {e}") from e

    async def fetch_one(self, query: str, *args: Any) -> Optional[Any]:
        """
        Execute a SELECT query and return a single row, or None.

        Args:
            query: SQL query string using $1, $2 placeholders.
            *args: Query parameters.

        Returns:
            A single row, or None if no rows matched.

        Raises:
            AsyncQueryError: If the query fails.
        """
        self._check_connection()
        adapted_query, adapted_args = self._adapt_query(query, args)
        try:
            if self.db_type == "postgres":
                return await self._connection.fetchrow(adapted_query, *adapted_args)

            elif self.db_type == "sqlite":
                async with self._connection.execute(
                    adapted_query, adapted_args
                ) as cursor:
                    return await cursor.fetchone()

            elif self.db_type in ("mysql", "sqlserver"):
                async with self._connection.cursor() as cursor:
                    await cursor.execute(adapted_query, adapted_args)
                    return await cursor.fetchone()

            elif self.db_type == "oracle":
                cursor = self._connection.cursor()
                await cursor.execute(adapted_query, adapted_args)
                return await cursor.fetchone()

            return None

        except Exception as e:
            raise AsyncQueryError(f"fetch_one failed: {e}") from e

    async def fetch_all(self, query: str, *args: Any) -> list[Any]:
        """
        Execute a SELECT query and return all rows.

        Args:
            query: SQL query string using $1, $2 placeholders.
            *args: Query parameters.

        Returns:
            A list of rows (empty list if no rows matched).

        Raises:
            AsyncQueryError: If the query fails.
        """
        self._check_connection()
        adapted_query, adapted_args = self._adapt_query(query, args)
        try:
            if self.db_type == "postgres":
                return await self._connection.fetch(adapted_query, *adapted_args)

            elif self.db_type == "sqlite":
                async with self._connection.execute(
                    adapted_query, adapted_args
                ) as cursor:
                    return await cursor.fetchall()

            elif self.db_type in ("mysql", "sqlserver"):
                async with self._connection.cursor() as cursor:
                    await cursor.execute(adapted_query, adapted_args)
                    return await cursor.fetchall()

            elif self.db_type == "oracle":
                cursor = self._connection.cursor()
                await cursor.execute(adapted_query, adapted_args)
                return await cursor.fetchall()

            return []

        except Exception as e:
            raise AsyncQueryError(f"fetch_all failed: {e}") from e

    async def fetch_val(self, query: str, *args: Any) -> Optional[Any]:
        """
        Execute a SELECT query and return a single scalar value.

        Useful for COUNT, SUM, or any query returning one value::

            count = await db.fetch_val("SELECT COUNT(*) FROM users")

        Args:
            query: SQL query string using $1, $2 placeholders.
            *args: Query parameters.

        Returns:
            A single scalar value, or None.

        Raises:
            AsyncQueryError: If the query fails.
        """
        self._check_connection()
        adapted_query, adapted_args = self._adapt_query(query, args)
        try:
            if self.db_type == "postgres":
                return await self._connection.fetchval(adapted_query, *adapted_args)

            elif self.db_type == "sqlite":
                async with self._connection.execute(
                    adapted_query, adapted_args
                ) as cursor:
                    row = await cursor.fetchone()
                    return row[0] if row else None

            elif self.db_type in ("mysql", "sqlserver"):
                async with self._connection.cursor() as cursor:
                    await cursor.execute(adapted_query, adapted_args)
                    row = await cursor.fetchone()
                    return row[0] if row else None

            elif self.db_type == "oracle":
                cursor = self._connection.cursor()
                await cursor.execute(adapted_query, adapted_args)
                row = await cursor.fetchone()
                return row[0] if row else None

            return None

        except Exception as e:
            raise AsyncQueryError(f"fetch_val failed: {e}") from e

    async def execute_many(self, query: str, args_list: list[tuple]) -> None:
        """
        Execute a SQL statement multiple times with different parameters.
        Efficient for bulk inserts::

            await db.execute_many(
                "INSERT INTO users (id, name) VALUES ($1, $2)",
                [(1, "Alice"), (2, "Bob"), (3, "Charlie")]
            )

        Args:
            query:     SQL query string using $1, $2 placeholders.
            args_list: List of parameter tuples.

        Raises:
            AsyncQueryError: If the operation fails.
        """
        self._check_connection()
        if not args_list:
            return
        try:
            if self.db_type == "postgres":
                await self._connection.executemany(query, args_list)

            elif self.db_type == "sqlite":
                import re

                adapted = re.sub(r"\$\d+", "?", query)
                await self._connection.executemany(adapted, args_list)
                await self._connection.commit()

            elif self.db_type in ("mysql", "sqlserver"):
                import re

                adapted = re.sub(r"\$\d+", "%s", query)
                async with self._connection.cursor() as cursor:
                    await cursor.executemany(adapted, args_list)
                await self._connection.commit()

            elif self.db_type == "oracle":
                import re

                def replace_placeholder(m: Any) -> str:
                    return f":{m.group(1)}"

                adapted = re.sub(r"\$(\d+)", replace_placeholder, query)
                cursor = self._connection.cursor()
                await cursor.executemany(adapted, args_list)
                await self._connection.commit()

            logger.debug("execute_many: %d rows", len(args_list))

        except Exception as e:
            raise AsyncQueryError(f"execute_many failed: {e}") from e

    # -----------------------------------------------------------------------
    # Transaction management
    # -----------------------------------------------------------------------

    async def begin_transaction(self) -> None:
        """
        Begin an explicit transaction.

        For PostgreSQL, use the transaction() context manager instead,
        which is the idiomatic asyncpg approach.

        Raises:
            AsyncQueryError: If the transaction cannot be started.
        """
        self._check_connection()
        try:
            if self.db_type == "sqlite":
                await self._connection.execute("BEGIN")
            elif self.db_type == "mysql":
                await self._connection.begin()
            elif self.db_type == "sqlserver":
                async with self._connection.cursor() as cursor:
                    await cursor.execute("BEGIN TRANSACTION")
            elif self.db_type == "oracle":
                pass  # Oracle starts transactions implicitly
            elif self.db_type == "postgres":
                # asyncpg transactions are managed via connection.transaction()
                # Calling begin() manually is supported but the context manager
                # is preferred — see transaction() below
                self._pg_transaction = self._connection.transaction()
                await self._pg_transaction.start()
            logger.info("Transaction started on %s", self.db_type)
        except Exception as e:
            raise AsyncQueryError(f"Failed to begin transaction: {e}") from e

    async def commit_transaction(self) -> None:
        """Commit the current transaction."""
        self._check_connection()
        try:
            if self.db_type == "postgres":
                await self._pg_transaction.commit()
            else:
                await self._connection.commit()
            logger.info("Transaction committed on %s", self.db_type)
        except Exception as e:
            raise AsyncQueryError(f"Failed to commit transaction: {e}") from e

    async def rollback_transaction(self) -> None:
        """Roll back the current transaction."""
        self._check_connection()
        try:
            if self.db_type == "postgres":
                await self._pg_transaction.rollback()
            else:
                await self._connection.rollback()
            logger.info("Transaction rolled back on %s", self.db_type)
        except Exception as e:
            raise AsyncQueryError(f"Failed to rollback transaction: {e}") from e

    # -----------------------------------------------------------------------
    # Connection pooling
    # -----------------------------------------------------------------------

    async def setup_pool(self, min_size: int = 1, max_size: int = 10) -> None:
        """
        Set up an async connection pool.

        Supported for PostgreSQL and MySQL only.
        After calling this, use get_connection_from_pool() to acquire
        connections.

        Args:
            min_size: Minimum number of connections in the pool.
            max_size: Maximum number of connections in the pool.

        Raises:
            AsyncConnectionError: If pool setup fails or db_type
                                  does not support pooling.
        """
        try:
            if self.db_type == "postgres":
                import asyncpg

                self._pool = await asyncpg.create_pool(
                    host=self.host,
                    port=int(self.port or 5432),
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    min_size=min_size,
                    max_size=max_size,
                )
                logger.info(
                    "PostgreSQL async pool created (min=%d, max=%d)", min_size, max_size
                )

            elif self.db_type == "mysql":
                import aiomysql

                self._pool = await aiomysql.create_pool(
                    host=self.host or "localhost",
                    port=int(self.port or 3306),
                    user=self.user,
                    password=self.password or "",
                    db=self.database,
                    minsize=min_size,
                    maxsize=max_size,
                )
                logger.info(
                    "MySQL async pool created (min=%d, max=%d)", min_size, max_size
                )

            else:
                raise AsyncConnectionError(
                    f"Async connection pooling not supported for {self.db_type!r}. "
                    "Supported: postgres, mysql."
                )
        except AsyncConnectionError:
            raise
        except Exception as e:
            raise AsyncConnectionError(f"Failed to create async pool: {e}") from e

    async def close_pool(self) -> None:
        """Close the async connection pool."""
        if self._pool is not None:
            if self.db_type == "mysql":
                self._pool.close()
                await self._pool.wait_closed()
            else:
                await self._pool.close()
            self._pool = None
            logger.info("Async pool closed for %s", self.db_type)
