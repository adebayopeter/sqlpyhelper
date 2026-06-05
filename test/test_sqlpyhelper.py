"""
SQLPyHelper test suite.
All tests use mocking — no live database required.
Run with: pytest test/ -v
"""

from unittest.mock import MagicMock, patch

import pytest

from sqlpyhelper.db_helper import (
    BackupError,
    ConnectionError,
    QueryError,
    SQLPyHelper,
    _validate_identifier,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_db(db_type="sqlite", mock_connect=None):
    """
    Return a SQLPyHelper instance with the underlying driver mocked out.
    Patches the driver import inside db_helper so no real connection is made.
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    if mock_connect is not None:
        mock_connect.return_value = mock_conn

    with patch.dict(
        "os.environ",
        {
            "DB_TYPE": db_type,
            "DB_HOST": "localhost",
            "DB_USER": "user",
            "DB_PASSWORD": "password",
            "DB_NAME": "testdb",
        },
    ):
        if db_type == "sqlite":
            with patch("sqlite3.connect", return_value=mock_conn):
                db = SQLPyHelper(db_type="sqlite", database=":memory:")
        elif db_type == "postgres":
            with patch("psycopg2.connect", return_value=mock_conn):
                db = SQLPyHelper(
                    db_type="postgres",
                    host="localhost",
                    user="user",
                    password="pass",
                    database="testdb",
                )
        elif db_type == "mysql":
            with patch("mysql.connector.connect", return_value=mock_conn):
                db = SQLPyHelper(
                    db_type="mysql",
                    host="localhost",
                    user="user",
                    password="pass",
                    database="testdb",
                )
        elif db_type == "sqlserver":
            with patch("pyodbc.connect", return_value=mock_conn):
                db = SQLPyHelper(
                    db_type="sqlserver",
                    host="localhost",
                    user="user",
                    password="pass",
                    database="testdb",
                    driver="ODBC Driver 17 for SQL Server",
                )
        elif db_type == "oracle":
            with patch("oracledb.connect", return_value=mock_conn):
                with patch("oracledb.makedsn", return_value="mock_dsn"):
                    db = SQLPyHelper(
                        db_type="oracle",
                        host="localhost",
                        user="user",
                        password="pass",
                        database="testdb",
                        oracle_sid="XE",
                    )

    db.connection = mock_conn
    db.cursor = mock_cursor
    return db, mock_conn, mock_cursor


# ---------------------------------------------------------------------------
# _validate_identifier
# ---------------------------------------------------------------------------


class TestValidateIdentifier:

    def test_valid_simple_name(self):
        assert _validate_identifier("users") == "users"

    def test_valid_with_underscore(self):
        assert _validate_identifier("user_accounts") == "user_accounts"

    def test_valid_with_numbers(self):
        assert _validate_identifier("table_1") == "table_1"

    def test_valid_uppercase(self):
        assert _validate_identifier("Users") == "Users"

    def test_rejects_space(self):
        with pytest.raises(ValueError, match="Invalid SQL identifier"):
            _validate_identifier("user accounts")

    def test_rejects_hyphen(self):
        with pytest.raises(ValueError, match="Invalid SQL identifier"):
            _validate_identifier("user-accounts")

    def test_rejects_semicolon(self):
        with pytest.raises(ValueError, match="Invalid SQL identifier"):
            _validate_identifier("users; DROP TABLE users")

    def test_rejects_empty_string(self):
        with pytest.raises(ValueError, match="Invalid SQL identifier"):
            _validate_identifier("")

    def test_rejects_starts_with_digit(self):
        with pytest.raises(ValueError, match="Invalid SQL identifier"):
            _validate_identifier("1table")

    def test_rejects_sql_injection_attempt(self):
        with pytest.raises(ValueError, match="Invalid SQL identifier"):
            _validate_identifier("users' OR '1'='1")


# ---------------------------------------------------------------------------
# __init__ — connection setup
# ---------------------------------------------------------------------------


class TestInit:

    def test_sqlite_connects(self):
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = MagicMock()
        with patch("sqlite3.connect", return_value=mock_conn) as mock_connect:
            SQLPyHelper(db_type="sqlite", database=":memory:")
            mock_connect.assert_called_once_with(":memory:")

    def test_postgres_connects(self):
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = MagicMock()
        with patch("psycopg2.connect", return_value=mock_conn) as mock_connect:
            SQLPyHelper(
                db_type="postgres",
                host="localhost",
                user="user",
                password="pass",
                database="testdb",
            )
            mock_connect.assert_called_once()

    def test_mysql_connects(self):
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = MagicMock()
        with patch("mysql.connector.connect", return_value=mock_conn) as mock_connect:
            SQLPyHelper(
                db_type="mysql",
                host="localhost",
                user="user",
                password="pass",
                database="testdb",
            )
            mock_connect.assert_called_once()

    def test_unsupported_db_type_raises(self):
        with pytest.raises(ValueError, match="Unsupported database type"):
            with patch("sqlite3.connect"):
                SQLPyHelper(db_type="mongodb", database="testdb")

    def test_missing_database_raises(self):
        with pytest.raises(ValueError, match="Missing required database configuration"):
            with patch.dict("os.environ", {}, clear=True):
                SQLPyHelper(db_type="sqlite", database="")

    def test_init_kwargs_stored(self):
        db, _, _ = make_db("sqlite")
        assert db._init_kwargs["db_type"] == "sqlite"
        assert db._init_kwargs["database"] == ":memory:"


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


class TestContextManager:

    def test_enter_returns_self(self):
        db, _, _ = make_db("sqlite")
        assert db.__enter__() is db

    def test_exit_calls_close(self):
        db, mock_conn, mock_cursor = make_db("sqlite")
        db.__exit__(None, None, None)
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_exit_returns_false(self):
        db, _, _ = make_db("sqlite")
        result = db.__exit__(None, None, None)
        assert result is False

    def test_with_statement(self):
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = MagicMock()
        with patch("sqlite3.connect", return_value=mock_conn):
            with SQLPyHelper(db_type="sqlite", database=":memory:") as db:
                assert db is not None
            mock_conn.close.assert_called_once()


# ---------------------------------------------------------------------------
# execute_query
# ---------------------------------------------------------------------------


class TestExecuteQuery:

    def test_executes_without_params(self):
        db, mock_conn, mock_cursor = make_db("sqlite")
        db.execute_query("SELECT 1")
        mock_cursor.execute.assert_called_once_with("SELECT 1")
        mock_conn.commit.assert_called_once()

    def test_executes_with_params(self):
        db, mock_conn, mock_cursor = make_db("sqlite")
        db.execute_query("SELECT * FROM users WHERE id = ?", (1,))
        mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM users WHERE id = ?", (1,)
        )

    def test_raises_query_error_on_failure(self):
        db, _, mock_cursor = make_db("sqlite")
        mock_cursor.execute.side_effect = Exception("syntax error")
        with pytest.raises(QueryError, match="Query failed"):
            db.execute_query("INVALID SQL")


# ---------------------------------------------------------------------------
# fetch_one / fetch_all
# ---------------------------------------------------------------------------


class TestFetch:

    def test_fetch_one_returns_row(self):
        db, _, mock_cursor = make_db("sqlite")
        mock_cursor.fetchone.return_value = (1, "Alice")
        result = db.fetch_one()
        assert result == (1, "Alice")

    def test_fetch_one_raises_on_error(self):
        db, _, mock_cursor = make_db("sqlite")
        mock_cursor.fetchone.side_effect = Exception("cursor error")
        with pytest.raises(QueryError, match="Failed to fetch row"):
            db.fetch_one()

    def test_fetch_all_returns_rows(self):
        db, _, mock_cursor = make_db("sqlite")
        mock_cursor.fetchall.return_value = [(1, "Alice"), (2, "Bob")]
        result = db.fetch_all()
        assert len(result) == 2
        assert result[0] == (1, "Alice")

    def test_fetch_all_raises_on_error(self):
        db, _, mock_cursor = make_db("sqlite")
        mock_cursor.fetchall.side_effect = Exception("cursor error")
        with pytest.raises(QueryError, match="Failed to fetch rows"):
            db.fetch_all()


# ---------------------------------------------------------------------------
# fetch_by_param
# ---------------------------------------------------------------------------


class TestFetchByParam:

    def test_fetches_with_sqlite_placeholder(self):
        db, _, mock_cursor = make_db("sqlite")
        mock_cursor.fetchall.return_value = [(1, "Alice")]
        result = db.fetch_by_param("users", "name", "Alice")
        call_args = mock_cursor.execute.call_args
        assert "?" in call_args[0][0]
        assert result == [(1, "Alice")]

    def test_fetches_with_mysql_placeholder(self):
        db, _, mock_cursor = make_db("mysql")
        mock_cursor.fetchall.return_value = [(1, "Alice")]
        db.fetch_by_param("users", "name", "Alice")
        call_args = mock_cursor.execute.call_args
        assert "%s" in call_args[0][0]

    def test_rejects_invalid_table_name(self):
        db, _, _ = make_db("sqlite")
        with pytest.raises(QueryError):
            db.fetch_by_param("users; DROP TABLE users", "name", "Alice")

    def test_rejects_invalid_column_name(self):
        db, _, _ = make_db("sqlite")
        with pytest.raises(QueryError):
            db.fetch_by_param("users", "name' OR '1'='1", "Alice")


# ---------------------------------------------------------------------------
# close
# ---------------------------------------------------------------------------


class TestClose:

    def test_close_calls_cursor_and_connection(self):
        db, mock_conn, mock_cursor = make_db("sqlite")
        db.close()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_close_raises_connection_error_on_failure(self):
        db, mock_conn, mock_cursor = make_db("sqlite")
        mock_cursor.close.side_effect = Exception("already closed")
        with pytest.raises(ConnectionError, match="Failed to close connection"):
            db.close()


# ---------------------------------------------------------------------------
# create_table
# ---------------------------------------------------------------------------


class TestCreateTable:

    def test_creates_table_with_valid_columns(self):
        db, _, mock_cursor = make_db("sqlite")
        db.create_table("users", {"id": "INTEGER PRIMARY KEY", "name": "TEXT"})
        call_args = mock_cursor.execute.call_args[0][0]
        assert "CREATE TABLE IF NOT EXISTS users" in call_args
        assert "id" in call_args
        assert "name" in call_args

    def test_rejects_invalid_table_name(self):
        db, _, _ = make_db("sqlite")
        with pytest.raises(QueryError):
            db.create_table("users; DROP TABLE users", {"id": "INTEGER"})

    def test_rejects_invalid_column_name(self):
        db, _, _ = make_db("sqlite")
        with pytest.raises(QueryError):
            db.create_table("users", {"id; DROP TABLE users": "INTEGER"})


# ---------------------------------------------------------------------------
# insert_bulk
# ---------------------------------------------------------------------------


class TestInsertBulk:

    def test_inserts_multiple_rows(self):
        db, _, mock_cursor = make_db("sqlite")
        data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        db.insert_bulk("users", data)
        mock_cursor.executemany.assert_called_once()
        call_args = mock_cursor.executemany.call_args
        assert "INSERT INTO users" in call_args[0][0]
        assert len(call_args[0][1]) == 2

    def test_uses_correct_placeholder_sqlite(self):
        db, _, mock_cursor = make_db("sqlite")
        db.insert_bulk("users", [{"id": 1, "name": "Alice"}])
        query = mock_cursor.executemany.call_args[0][0]
        assert "?" in query

    def test_uses_correct_placeholder_mysql(self):
        db, _, mock_cursor = make_db("mysql")
        db.insert_bulk("users", [{"id": 1, "name": "Alice"}])
        query = mock_cursor.executemany.call_args[0][0]
        assert "%s" in query

    def test_rejects_invalid_table_name(self):
        db, _, _ = make_db("sqlite")
        with pytest.raises(QueryError):
            db.insert_bulk("users; DROP TABLE users", [{"id": 1}])


# ---------------------------------------------------------------------------
# backup_table
# ---------------------------------------------------------------------------


class TestBackupTable:

    def test_writes_csv_file(self, tmp_path):
        db, _, mock_cursor = make_db("sqlite")
        mock_cursor.fetchall.return_value = [(1, "Alice"), (2, "Bob")]
        mock_cursor.description = [("id",), ("name",)]
        backup_file = str(tmp_path / "backup.csv")
        db.backup_table("users", backup_file)
        with open(backup_file) as f:
            contents = f.read()
        assert "id" in contents
        assert "Alice" in contents

    def test_rejects_invalid_table_name(self, tmp_path):
        db, _, _ = make_db("sqlite")
        with pytest.raises(BackupError):
            db.backup_table("users; DROP TABLE users", str(tmp_path / "backup.csv"))


# ---------------------------------------------------------------------------
# transaction management
# ---------------------------------------------------------------------------


class TestTransactions:

    def test_begin_transaction_sqlite(self):
        db, _, mock_cursor = make_db("sqlite")
        db.begin_transaction()
        mock_cursor.execute.assert_called_with("BEGIN")

    def test_begin_transaction_mysql(self):
        db, _, mock_cursor = make_db("mysql")
        db.begin_transaction()
        mock_cursor.execute.assert_called_with("START TRANSACTION")

    def test_commit_transaction(self):
        db, mock_conn, _ = make_db("sqlite")
        db.commit_transaction()
        mock_conn.commit.assert_called()

    def test_rollback_transaction(self):
        db, mock_conn, _ = make_db("sqlite")
        db.rollback_transaction()
        mock_conn.rollback.assert_called_once()

    def test_rollback_raises_on_failure(self):
        db, mock_conn, _ = make_db("sqlite")
        mock_conn.rollback.side_effect = Exception("rollback error")
        with pytest.raises(QueryError, match="Failed to rollback transaction"):
            db.rollback_transaction()


# ---------------------------------------------------------------------------
# reconnect
# ---------------------------------------------------------------------------


class TestReconnect:

    def test_reconnect_closes_and_reinits(self):
        db, mock_conn, _ = make_db("sqlite")
        original_close = mock_conn.close
        new_mock_conn = MagicMock()
        new_mock_conn.cursor.return_value = MagicMock()
        with patch("sqlite3.connect", return_value=new_mock_conn):
            db.reconnect()
        original_close.assert_called_once()

    def test_reconnect_raises_on_failure(self):
        db, mock_conn, _ = make_db("sqlite")
        mock_conn.close.side_effect = Exception("connection lost")
        with pytest.raises(ConnectionError, match="Reconnection failed"):
            db.reconnect()


# ---------------------------------------------------------------------------
# insert_dynamic
# ---------------------------------------------------------------------------


class TestInsertDynamic:

    def test_inserts_with_correct_columns(self):
        db, _, mock_cursor = make_db("sqlite")
        db.insert_dynamic("users", {"id": 1, "name": "Alice"})
        call_args = mock_cursor.execute.call_args[0][0]
        assert "INSERT INTO users" in call_args
        assert "id" in call_args
        assert "name" in call_args

    def test_uses_sqlite_placeholder(self):
        db, _, mock_cursor = make_db("sqlite")
        db.insert_dynamic("users", {"id": 1, "name": "Alice"})
        query = mock_cursor.execute.call_args[0][0]
        assert "?" in query

    def test_uses_mysql_placeholder(self):
        db, _, mock_cursor = make_db("mysql")
        db.insert_dynamic("users", {"id": 1, "name": "Alice"})
        query = mock_cursor.execute.call_args[0][0]
        assert "%s" in query

    def test_rejects_invalid_table_name(self):
        db, _, _ = make_db("sqlite")
        with pytest.raises(Exception):
            db.insert_dynamic("users; DROP TABLE users", {"id": 1})


# ---------------------------------------------------------------------------
# connection pool
# ---------------------------------------------------------------------------


class TestConnectionPool:

    def test_postgres_pool_setup(self):
        db, _, _ = make_db("postgres")
        mock_pool = MagicMock()
        with patch("psycopg2.pool.SimpleConnectionPool", return_value=mock_pool):
            db.setup_connection_pool()
        assert db.pool == mock_pool

    def test_mysql_pool_setup(self):
        db, _, _ = make_db("mysql")
        mock_pool = MagicMock()
        with patch(
            "mysql.connector.pooling.MySQLConnectionPool", return_value=mock_pool
        ):
            db.setup_connection_pool()
        assert db.pool == mock_pool

    def test_unsupported_db_raises(self):
        db, _, _ = make_db("sqlite")
        with pytest.raises(ConnectionError, match="Failed to set up connection pool"):
            db.setup_connection_pool()

    def test_return_connection_raises_when_no_pool(self):
        db, _, _ = make_db("sqlite")
        db.pool = None
        with pytest.raises(RuntimeError, match="No connection pool initialised"):
            db.return_connection_to_pool()

    def test_postgres_return_calls_putconn(self):
        db, mock_conn, _ = make_db("postgres")
        mock_pool = MagicMock()
        db.pool = mock_pool
        db.return_connection_to_pool(mock_conn)
        mock_pool.putconn.assert_called_once_with(mock_conn)

    def test_oracle_return_calls_release(self):
        db, mock_conn, _ = make_db("oracle")
        mock_pool = MagicMock()
        db.pool = mock_pool
        db.return_connection_to_pool(mock_conn)
        mock_pool.release.assert_called_once_with(mock_conn)
