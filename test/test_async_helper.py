"""
Tests for sqlpyhelper.async_helper
All tests use mocking — no live database required.
Uses pytest-asyncio for async test support.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sqlpyhelper.async_helper import (
    AsyncConnectionError,
    AsyncQueryError,
    AsyncSQLPyHelper,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_async_db(db_type: str = "sqlite") -> AsyncSQLPyHelper:
    """Create an AsyncSQLPyHelper instance without connecting."""
    kwargs = {"db_type": db_type, "database": "test.db"}
    if db_type != "sqlite":
        kwargs.update(
            {
                "host": "localhost",
                "user": "user",
                "password": "pass",
                "database": "testdb",
            }
        )
    if db_type == "oracle":
        kwargs["oracle_sid"] = "XE"
    if db_type == "sqlserver":
        kwargs["driver"] = "ODBC Driver 17 for SQL Server"
    return AsyncSQLPyHelper(**kwargs)


def attach_mock_connection(db: AsyncSQLPyHelper) -> MagicMock:
    """Attach a mock connection to an AsyncSQLPyHelper instance."""
    mock_conn = MagicMock()
    mock_conn.close = AsyncMock()
    mock_conn.commit = AsyncMock()
    mock_conn.rollback = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_conn.executemany = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=[])
    mock_conn.fetchrow = AsyncMock(return_value=None)
    mock_conn.fetchval = AsyncMock(return_value=None)
    db._connection = mock_conn
    return mock_conn


# ---------------------------------------------------------------------------
# __init__ validation
# ---------------------------------------------------------------------------


class TestInit:
    def test_missing_database_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(
                ValueError, match="Missing required database configuration"
            ):
                AsyncSQLPyHelper(db_type="sqlite", database="")

    def test_missing_db_type_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(
                ValueError, match="Missing required database configuration"
            ):
                AsyncSQLPyHelper(db_type="", database="test.db")

    def test_unsupported_db_type_raises(self):
        with pytest.raises(ValueError, match="Unsupported database type"):
            AsyncSQLPyHelper(db_type="mongodb", database="test")

    def test_valid_sqlite_init(self):
        db = AsyncSQLPyHelper(db_type="sqlite", database="test.db")
        assert db.db_type == "sqlite"
        assert db.database == "test.db"
        assert db._connection is None

    def test_valid_postgres_init(self):
        db = AsyncSQLPyHelper(
            db_type="postgres",
            host="localhost",
            user="user",
            password="pass",
            database="testdb",
        )
        assert db.db_type == "postgres"


# ---------------------------------------------------------------------------
# connect / close
# ---------------------------------------------------------------------------


class TestConnect:
    @pytest.mark.asyncio
    async def test_sqlite_connect(self):
        db = make_async_db("sqlite")
        mock_conn = MagicMock()
        mock_conn.close = AsyncMock()
        with patch("aiosqlite.connect", new_callable=AsyncMock, return_value=mock_conn):
            await db.connect()
        assert db._connection is mock_conn

    @pytest.mark.asyncio
    async def test_postgres_connect(self):
        db = make_async_db("postgres")
        mock_conn = MagicMock()
        mock_conn.close = AsyncMock()
        with patch("asyncpg.connect", new_callable=AsyncMock, return_value=mock_conn):
            await db.connect()
        assert db._connection is mock_conn

    @pytest.mark.asyncio
    async def test_mysql_connect(self):
        db = make_async_db("mysql")
        mock_conn = MagicMock()
        mock_conn.close = AsyncMock()
        with patch("aiomysql.connect", new_callable=AsyncMock, return_value=mock_conn):
            await db.connect()
        assert db._connection is mock_conn

    @pytest.mark.asyncio
    async def test_connect_failure_raises_async_connection_error(self):
        db = make_async_db("sqlite")
        with patch("aiosqlite.connect", side_effect=Exception("disk full")):
            with pytest.raises(AsyncConnectionError, match="Failed to connect"):
                await db.connect()

    @pytest.mark.asyncio
    async def test_close(self):
        db = make_async_db("sqlite")
        mock_conn = attach_mock_connection(db)
        await db.close()
        mock_conn.close.assert_called_once()
        assert db._connection is None

    @pytest.mark.asyncio
    async def test_close_raises_on_failure(self):
        db = make_async_db("sqlite")
        mock_conn = attach_mock_connection(db)
        mock_conn.close.side_effect = Exception("already closed")
        with pytest.raises(AsyncConnectionError, match="Failed to close"):
            await db.close()


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


class TestContextManager:
    @pytest.mark.asyncio
    async def test_aenter_returns_self(self):
        db = make_async_db("sqlite")
        mock_conn = MagicMock()
        mock_conn.close = AsyncMock()
        with patch("aiosqlite.connect", new_callable=AsyncMock, return_value=mock_conn):
            result = await db.__aenter__()
        assert result is db

    @pytest.mark.asyncio
    async def test_aexit_closes_connection(self):
        db = make_async_db("sqlite")
        mock_conn = attach_mock_connection(db)
        await db.__aexit__(None, None, None)
        mock_conn.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_aexit_returns_false(self):
        db = make_async_db("sqlite")
        attach_mock_connection(db)
        result = await db.__aexit__(None, None, None)
        assert result is False

    @pytest.mark.asyncio
    async def test_async_with_statement(self):
        mock_conn = MagicMock()
        mock_conn.close = AsyncMock()
        with patch("aiosqlite.connect", new_callable=AsyncMock, return_value=mock_conn):
            async with AsyncSQLPyHelper(db_type="sqlite", database="test.db") as db:
                assert db._connection is mock_conn
        mock_conn.close.assert_called_once()


# ---------------------------------------------------------------------------
# _check_connection
# ---------------------------------------------------------------------------


class TestCheckConnection:
    def test_raises_when_no_connection(self):
        db = make_async_db("sqlite")
        with pytest.raises(AsyncConnectionError, match="No active connection"):
            db._check_connection()

    def test_passes_when_connected(self):
        db = make_async_db("sqlite")
        attach_mock_connection(db)
        db._check_connection()  # should not raise


# ---------------------------------------------------------------------------
# _adapt_query
# ---------------------------------------------------------------------------


class TestAdaptQuery:
    def test_postgres_passes_through(self):
        db = make_async_db("postgres")
        q, args = db._adapt_query("SELECT $1", (1,))
        assert q == "SELECT $1"

    def test_sqlite_replaces_with_question_mark(self):
        db = make_async_db("sqlite")
        q, args = db._adapt_query("SELECT $1, $2", (1, 2))
        assert q == "SELECT ?, ?"

    def test_mysql_replaces_with_percent_s(self):
        db = make_async_db("mysql")
        q, args = db._adapt_query("SELECT $1, $2", (1, 2))
        assert q == "SELECT %s, %s"

    def test_oracle_replaces_with_colon(self):
        db = AsyncSQLPyHelper(
            db_type="oracle",
            host="localhost",
            user="u",
            password="p",
            database="d",
            oracle_sid="XE",
        )
        q, args = db._adapt_query("SELECT $1, $2", (1, 2))
        assert q == "SELECT :1, :2"

    def test_empty_args_returns_unchanged(self):
        db = make_async_db("sqlite")
        q, args = db._adapt_query("SELECT 1", ())
        assert q == "SELECT 1"
        assert args == ()


# ---------------------------------------------------------------------------
# execute
# ---------------------------------------------------------------------------


class TestExecute:
    @pytest.mark.asyncio
    async def test_sqlite_execute(self):
        db = make_async_db("sqlite")
        mock_conn = attach_mock_connection(db)
        await db.execute("CREATE TABLE users (id INTEGER)")
        mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_postgres_execute(self):
        db = make_async_db("postgres")
        mock_conn = attach_mock_connection(db)
        await db.execute("INSERT INTO users VALUES ($1)", 1)
        mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_async_query_error_on_failure(self):
        db = make_async_db("sqlite")
        mock_conn = attach_mock_connection(db)
        mock_conn.execute.side_effect = Exception("disk full")
        with pytest.raises(AsyncQueryError, match="Query failed"):
            await db.execute("INSERT INTO users VALUES ($1)", 1)

    @pytest.mark.asyncio
    async def test_raises_when_not_connected(self):
        db = make_async_db("sqlite")
        with pytest.raises(AsyncConnectionError, match="No active connection"):
            await db.execute("SELECT 1")


# ---------------------------------------------------------------------------
# fetch_one
# ---------------------------------------------------------------------------


class TestFetchOne:
    @pytest.mark.asyncio
    async def test_postgres_fetch_one(self):
        db = make_async_db("postgres")
        mock_conn = attach_mock_connection(db)
        mock_conn.fetchrow.return_value = {"id": 1, "name": "Alice"}
        result = await db.fetch_one("SELECT * FROM users WHERE id = $1", 1)
        assert result == {"id": 1, "name": "Alice"}

    @pytest.mark.asyncio
    async def test_raises_on_failure(self):
        db = make_async_db("postgres")
        mock_conn = attach_mock_connection(db)
        mock_conn.fetchrow.side_effect = Exception("connection lost")
        with pytest.raises(AsyncQueryError, match="fetch_one failed"):
            await db.fetch_one("SELECT * FROM users")

    @pytest.mark.asyncio
    async def test_raises_when_not_connected(self):
        db = make_async_db("sqlite")
        with pytest.raises(AsyncConnectionError):
            await db.fetch_one("SELECT 1")


# ---------------------------------------------------------------------------
# fetch_all
# ---------------------------------------------------------------------------


class TestFetchAll:
    @pytest.mark.asyncio
    async def test_postgres_fetch_all(self):
        db = make_async_db("postgres")
        mock_conn = attach_mock_connection(db)
        mock_conn.fetch.return_value = [{"id": 1}, {"id": 2}]
        result = await db.fetch_all("SELECT * FROM users")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_raises_on_failure(self):
        db = make_async_db("postgres")
        mock_conn = attach_mock_connection(db)
        mock_conn.fetch.side_effect = Exception("timeout")
        with pytest.raises(AsyncQueryError, match="fetch_all failed"):
            await db.fetch_all("SELECT * FROM users")

    @pytest.mark.asyncio
    async def test_raises_when_not_connected(self):
        db = make_async_db("sqlite")
        with pytest.raises(AsyncConnectionError):
            await db.fetch_all("SELECT 1")


# ---------------------------------------------------------------------------
# fetch_val
# ---------------------------------------------------------------------------


class TestFetchVal:
    @pytest.mark.asyncio
    async def test_postgres_fetch_val(self):
        db = make_async_db("postgres")
        mock_conn = attach_mock_connection(db)
        mock_conn.fetchval.return_value = 42
        result = await db.fetch_val("SELECT COUNT(*) FROM users")
        assert result == 42

    @pytest.mark.asyncio
    async def test_raises_on_failure(self):
        db = make_async_db("postgres")
        mock_conn = attach_mock_connection(db)
        mock_conn.fetchval.side_effect = Exception("error")
        with pytest.raises(AsyncQueryError, match="fetch_val failed"):
            await db.fetch_val("SELECT COUNT(*) FROM users")


# ---------------------------------------------------------------------------
# execute_many
# ---------------------------------------------------------------------------


class TestExecuteMany:
    @pytest.mark.asyncio
    async def test_postgres_execute_many(self):
        db = make_async_db("postgres")
        mock_conn = attach_mock_connection(db)
        mock_conn.executemany = AsyncMock()
        await db.execute_many(
            "INSERT INTO users VALUES ($1, $2)", [(1, "Alice"), (2, "Bob")]
        )
        mock_conn.executemany.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_list_does_nothing(self):
        db = make_async_db("postgres")
        mock_conn = attach_mock_connection(db)
        await db.execute_many("INSERT INTO users VALUES ($1)", [])
        mock_conn.executemany.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_on_failure(self):
        db = make_async_db("postgres")
        mock_conn = attach_mock_connection(db)
        mock_conn.executemany.side_effect = Exception("error")
        with pytest.raises(AsyncQueryError, match="execute_many failed"):
            await db.execute_many("INSERT INTO users VALUES ($1)", [(1,)])


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------


class TestTransactions:
    @pytest.mark.asyncio
    async def test_mysql_begin_calls_begin(self):
        db = make_async_db("mysql")
        mock_conn = attach_mock_connection(db)
        mock_conn.begin = AsyncMock()
        await db.begin_transaction()
        mock_conn.begin.assert_called_once()

    @pytest.mark.asyncio
    async def test_commit(self):
        db = make_async_db("mysql")
        mock_conn = attach_mock_connection(db)
        await db.commit_transaction()
        mock_conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_rollback(self):
        db = make_async_db("mysql")
        mock_conn = attach_mock_connection(db)
        await db.rollback_transaction()
        mock_conn.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_rollback_raises_on_failure(self):
        db = make_async_db("mysql")
        mock_conn = attach_mock_connection(db)
        mock_conn.rollback.side_effect = Exception("rollback error")
        with pytest.raises(AsyncQueryError, match="Failed to rollback"):
            await db.rollback_transaction()


# ---------------------------------------------------------------------------
# Connection pool
# ---------------------------------------------------------------------------


class TestPool:
    @pytest.mark.asyncio
    async def test_postgres_pool_setup(self):
        db = make_async_db("postgres")
        mock_pool = MagicMock()
        mock_pool.close = AsyncMock()
        with patch(
            "asyncpg.create_pool", new_callable=AsyncMock, return_value=mock_pool
        ):
            await db.setup_pool(min_size=1, max_size=5)
        assert db._pool is mock_pool

    @pytest.mark.asyncio
    async def test_mysql_pool_setup(self):
        db = make_async_db("mysql")
        mock_pool = MagicMock()
        mock_pool.close = MagicMock()
        mock_pool.wait_closed = AsyncMock()
        with patch(
            "aiomysql.create_pool", new_callable=AsyncMock, return_value=mock_pool
        ):
            await db.setup_pool(min_size=1, max_size=5)
        assert db._pool is mock_pool

    @pytest.mark.asyncio
    async def test_unsupported_db_raises(self):
        db = make_async_db("sqlite")
        with pytest.raises(AsyncConnectionError, match="not supported"):
            await db.setup_pool()

    @pytest.mark.asyncio
    async def test_close_pool_postgres(self):
        db = make_async_db("postgres")
        mock_pool = MagicMock()
        mock_pool.close = AsyncMock()
        db._pool = mock_pool
        await db.close_pool()
        mock_pool.close.assert_called_once()
        assert db._pool is None
