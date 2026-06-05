"""
Tests for sqlpyhelper.migration
All tests use mocking — no live database required.
"""

from unittest.mock import MagicMock

import pytest

from sqlpyhelper.migration import (
    MigrationError,
    _build_create_table_sql,
    _build_insert_sql,
    _map_type,
    _normalise_type,
    migrate_table,
)

# ---------------------------------------------------------------------------
# _normalise_type
# ---------------------------------------------------------------------------


class TestNormaliseType:
    def test_integer_variants(self):
        for t in ("int", "integer", "bigint", "smallint", "tinyint", "number"):
            assert _normalise_type(t) == "integer"

    def test_real_variants(self):
        for t in ("real", "float", "double", "double precision"):
            assert _normalise_type(t) == "real"

    def test_text_variants(self):
        for t in ("text", "clob", "nvarchar", "longtext"):
            assert _normalise_type(t) == "text"

    def test_varchar_variants(self):
        for t in ("varchar", "varchar2", "character varying", "char"):
            assert _normalise_type(t) == "varchar"

    def test_blob_variants(self):
        for t in ("blob", "bytea", "varbinary"):
            assert _normalise_type(t) == "blob"

    def test_bool_variants(self):
        for t in ("bool", "boolean"):
            assert _normalise_type(t) == "bool"

    def test_none_returns_text(self):
        assert _normalise_type(None) == "text"

    def test_unknown_returns_text(self):
        assert _normalise_type("jsonb") == "text"

    def test_strips_length_spec(self):
        assert _normalise_type("varchar(255)") == "varchar"
        assert _normalise_type("numeric(10,2)") == "numeric"


# ---------------------------------------------------------------------------
# _map_type
# ---------------------------------------------------------------------------


class TestMapType:
    def test_sqlite_integer(self):
        assert _map_type("integer", "sqlite") == "INTEGER"

    def test_postgres_integer(self):
        assert _map_type("integer", "postgres") == "INTEGER"

    def test_mysql_integer(self):
        assert _map_type("integer", "mysql") == "INT"

    def test_sqlserver_integer(self):
        assert _map_type("integer", "sqlserver") == "INT"

    def test_oracle_integer(self):
        assert _map_type("integer", "oracle") == "NUMBER"

    def test_postgres_text(self):
        assert _map_type("text", "postgres") == "TEXT"

    def test_sqlserver_text(self):
        assert _map_type("text", "sqlserver") == "NVARCHAR(MAX)"

    def test_oracle_text(self):
        assert _map_type("text", "oracle") == "CLOB"

    def test_unknown_db_falls_back(self):
        result = _map_type("integer", "unknowndb")
        assert result == "INTEGER"


# ---------------------------------------------------------------------------
# _build_create_table_sql
# ---------------------------------------------------------------------------


class TestBuildCreateTableSql:
    def test_sqlite_ddl(self):
        columns = [("id", "integer"), ("name", "text")]
        sql = _build_create_table_sql("users", columns, "sqlite")
        assert "CREATE TABLE IF NOT EXISTS users" in sql
        assert "id INTEGER" in sql
        assert "name TEXT" in sql

    def test_postgres_ddl(self):
        columns = [("id", "integer"), ("name", "varchar")]
        sql = _build_create_table_sql("users", columns, "postgres")
        assert "id INTEGER" in sql
        assert "name TEXT" in sql

    def test_mysql_ddl(self):
        columns = [("id", "integer"), ("name", "text")]
        sql = _build_create_table_sql("users", columns, "mysql")
        assert "id INT" in sql
        assert "name TEXT" in sql

    def test_sqlserver_ddl(self):
        columns = [("id", "integer"), ("notes", "text")]
        sql = _build_create_table_sql("orders", columns, "sqlserver")
        assert "CREATE TABLE IF NOT EXISTS orders" in sql
        assert "id INT" in sql
        assert "notes NVARCHAR(MAX)" in sql

    def test_oracle_ddl(self):
        columns = [("id", "integer"), ("name", "varchar")]
        sql = _build_create_table_sql("users", columns, "oracle")
        assert "id NUMBER" in sql
        assert "name VARCHAR2(255)" in sql


# ---------------------------------------------------------------------------
# _build_insert_sql
# ---------------------------------------------------------------------------


class TestBuildInsertSql:
    def test_sqlite_uses_question_mark(self):
        sql = _build_insert_sql("users", ["id", "name"], "sqlite")
        assert "?" in sql
        assert "%s" not in sql

    def test_postgres_uses_percent_s(self):
        sql = _build_insert_sql("users", ["id", "name"], "postgres")
        assert "%s" in sql
        assert "?" not in sql

    def test_correct_column_count(self):
        sql = _build_insert_sql("users", ["id", "name", "email"], "mysql")
        assert sql.count("%s") == 3

    def test_table_name_in_sql(self):
        sql = _build_insert_sql("orders", ["id", "item"], "postgres")
        assert "INSERT INTO orders" in sql


# ---------------------------------------------------------------------------
# migrate_table
# ---------------------------------------------------------------------------


def make_mock_db(db_type="sqlite"):
    """Create a mock SQLPyHelper instance."""
    db = MagicMock()
    db.db_type = db_type
    db.cursor = MagicMock()
    db.connection = MagicMock()
    return db


class TestMigrateTable:
    def test_basic_sqlite_to_postgres(self):
        source = make_mock_db("sqlite")
        target = make_mock_db("postgres")

        # Mock PRAGMA response for SQLite column info
        source.fetch_all.side_effect = [
            [(0, "id", "integer", 0, None, 1), (1, "name", "text", 0, None, 0)],
            [(1, "Alice"), (2, "Bob")],
        ]

        stats = migrate_table(source=source, target=target, table="users")

        assert stats["rows_migrated"] == 2
        assert stats["source_db"] == "sqlite"
        assert stats["target_db"] == "postgres"
        assert stats["table"] == "users"
        assert stats["batches"] == 1

    def test_create_table_called_when_flag_true(self):
        source = make_mock_db("sqlite")
        target = make_mock_db("postgres")

        source.fetch_all.side_effect = [
            [(0, "id", "integer", 0, None, 1)],
            [(1,), (2,)],
        ]

        migrate_table(source=source, target=target, table="users", create_table=True)
        target.execute_query.assert_called()
        first_call = target.execute_query.call_args_list[0][0][0]
        assert "CREATE TABLE IF NOT EXISTS users" in first_call

    def test_create_table_not_called_when_flag_false(self):
        source = make_mock_db("sqlite")
        target = make_mock_db("postgres")

        source.fetch_all.side_effect = [
            [(0, "id", "integer", 0, None, 1)],
            [(1,)],
        ]

        migrate_table(source=source, target=target, table="users", create_table=False)
        # execute_query should not be called on target for DDL
        for call in target.execute_query.call_args_list:
            assert "CREATE TABLE" not in str(call)

    def test_empty_table_returns_zero_rows(self):
        source = make_mock_db("sqlite")
        target = make_mock_db("postgres")

        source.fetch_all.side_effect = [
            [(0, "id", "integer", 0, None, 1)],
            [],
        ]

        stats = migrate_table(source=source, target=target, table="users")
        assert stats["rows_migrated"] == 0
        assert stats["batches"] == 0
        target.cursor.executemany.assert_not_called()

    def test_batching(self):
        source = make_mock_db("sqlite")
        target = make_mock_db("postgres")

        rows = [(i,) for i in range(25)]
        source.fetch_all.side_effect = [
            [(0, "id", "integer", 0, None, 1)],
            rows,
        ]

        stats = migrate_table(
            source=source, target=target, table="users", batch_size=10
        )
        assert stats["rows_migrated"] == 25
        assert stats["batches"] == 3
        assert target.cursor.executemany.call_count == 3

    def test_truncate_target_sqlite(self):
        source = make_mock_db("sqlite")
        target = make_mock_db("sqlite")

        source.fetch_all.side_effect = [
            [(0, "id", "integer", 0, None, 1)],
            [(1,)],
        ]

        migrate_table(source=source, target=target, table="users", truncate_target=True)
        delete_calls = [
            str(c) for c in target.execute_query.call_args_list if "DELETE" in str(c)
        ]
        assert len(delete_calls) == 1

    def test_truncate_target_postgres(self):
        source = make_mock_db("sqlite")
        target = make_mock_db("postgres")

        source.fetch_all.side_effect = [
            [(0, "id", "integer", 0, None, 1)],
            [(1,)],
        ]

        migrate_table(source=source, target=target, table="users", truncate_target=True)
        truncate_calls = [
            str(c) for c in target.execute_query.call_args_list if "TRUNCATE" in str(c)
        ]
        assert len(truncate_calls) == 1

    def test_raises_migration_error_on_empty_columns(self):
        source = make_mock_db("sqlite")
        target = make_mock_db("postgres")

        source.fetch_all.return_value = []

        with pytest.raises(MigrationError, match="not found in source database"):
            migrate_table(source=source, target=target, table="nonexistent")

    def test_raises_migration_error_on_db_failure(self):
        source = make_mock_db("sqlite")
        target = make_mock_db("postgres")

        source.fetch_all.side_effect = Exception("connection lost")

        with pytest.raises(MigrationError, match="Migration of 'users' failed"):
            migrate_table(source=source, target=target, table="users")

    def test_returns_correct_stats_structure(self):
        source = make_mock_db("mysql")
        target = make_mock_db("sqlserver")

        source.fetch_all.side_effect = [
            [("id", "int"), ("name", "varchar")],
            [(1, "Alice"), (2, "Bob"), (3, "Charlie")],
        ]

        stats = migrate_table(source=source, target=target, table="customers")
        assert set(stats.keys()) == {
            "table",
            "rows_migrated",
            "batches",
            "source_db",
            "target_db",
        }
        assert stats["source_db"] == "mysql"
        assert stats["target_db"] == "sqlserver"
