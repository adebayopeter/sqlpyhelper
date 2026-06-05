"""
sqlpyhelper.migration
~~~~~~~~~~~~~~~~~~~~~
Cross-database table migration utilities.

Copies data (and optionally schema) from one database to another.
Supports SQLite, PostgreSQL, MySQL, SQL Server, and Oracle.

Example usage::

    from sqlpyhelper.db_helper import SQLPyHelper
    from sqlpyhelper.migration import migrate_table

    with SQLPyHelper(db_type="sqlite", database="local.db") as source:
        with SQLPyHelper(db_type="postgres", host="localhost",
                         user="user", password="pass",
                         database="mydb") as target:

            migrate_table(
                source=source,
                target=target,
                table="users",
            )
"""

import logging
from typing import Any, Optional

logger = logging.getLogger("sqlpyhelper.migration")


class MigrationError(Exception):
    """Raised when a migration operation fails."""


# ---------------------------------------------------------------------------
# Type mapping
# ---------------------------------------------------------------------------

# Maps (source_db_type, generic_type) -> target SQL type string.
# Generic types are normalised from the source cursor description.


_TYPE_MAP: dict[str, dict[str, str]] = {
    "sqlite": {
        "integer": "INTEGER",
        "real": "REAL",
        "text": "TEXT",
        "blob": "BLOB",
        "numeric": "NUMERIC",
    },
    "postgres": {
        "integer": "INTEGER",
        "real": "DOUBLE PRECISION",
        "text": "TEXT",
        "blob": "BYTEA",
        "numeric": "NUMERIC",
        "varchar": "TEXT",
        "bool": "BOOLEAN",
        "date": "DATE",
        "timestamp": "TIMESTAMP",
    },
    "mysql": {
        "integer": "INT",
        "real": "DOUBLE",
        "text": "TEXT",
        "blob": "BLOB",
        "numeric": "DECIMAL",
        "varchar": "VARCHAR(255)",
        "bool": "TINYINT(1)",
        "date": "DATE",
        "timestamp": "DATETIME",
    },
    "sqlserver": {
        "integer": "INT",
        "real": "FLOAT",
        "text": "NVARCHAR(MAX)",
        "blob": "VARBINARY(MAX)",
        "numeric": "DECIMAL",
        "varchar": "NVARCHAR(255)",
        "bool": "BIT",
        "date": "DATE",
        "timestamp": "DATETIME2",
    },
    "oracle": {
        "integer": "NUMBER",
        "real": "FLOAT",
        "text": "CLOB",
        "blob": "BLOB",
        "numeric": "NUMBER",
        "varchar": "VARCHAR2(255)",
        "bool": "NUMBER(1)",
        "date": "DATE",
        "timestamp": "TIMESTAMP",
    },
}


def _normalise_type(raw_type: Optional[str]) -> str:
    """
    Normalise a raw column type string from a cursor description
    into a generic type key used for cross-database mapping.
    """
    if raw_type is None:
        return "text"
    t = raw_type.lower().split("(")[0].strip()
    if t in (
        "int",
        "integer",
        "int4",
        "int8",
        "bigint",
        "smallint",
        "tinyint",
        "number",
    ):
        return "integer"
    if t in ("real", "float", "double", "double precision", "float4", "float8"):
        return "real"
    if t in (
        "text",
        "clob",
        "nvarchar",
        "nvarchar2",
        "ntext",
        "longtext",
        "mediumtext",
    ):
        return "text"
    if t in ("varchar", "varchar2", "character varying", "char", "nchar"):
        return "varchar"
    if t in ("blob", "bytea", "varbinary", "binary", "longblob", "mediumblob"):
        return "blob"
    if t in ("numeric", "decimal"):
        return "numeric"
    if t in ("bool", "boolean"):
        return "bool"
    if t in ("date",):
        return "date"
    if t in ("timestamp", "datetime", "datetime2", "timestamp without time zone"):
        return "timestamp"
    return "text"  # safe fallback


def _map_type(raw_type: Optional[str], target_db: str) -> str:
    """Map a source column type to the appropriate type for the target database."""
    generic = _normalise_type(raw_type)
    target_types = _TYPE_MAP.get(target_db, _TYPE_MAP["sqlite"])
    return target_types.get(generic, "TEXT")


def _get_column_info(source: Any, table: str) -> list[tuple[str, str]]:
    """
    Return a list of (column_name, raw_type_string) tuples
    by inspecting the source database schema.
    """
    db_type = source.db_type

    if db_type == "sqlite":
        source.execute_query(f"PRAGMA table_info({table})")
        rows = source.fetch_all()
        # PRAGMA table_info returns: (cid, name, type, notnull, dflt_value, pk)
        return [(row[1], row[2]) for row in rows]

    elif db_type == "postgres":
        source.execute_query(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
            """,
            (table,),
        )
        return source.fetch_all()

    elif db_type == "mysql":
        source.execute_query(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = %s AND table_schema = DATABASE()
            ORDER BY ordinal_position
            """,
            (table,),
        )
        return source.fetch_all()

    elif db_type == "sqlserver":
        source.execute_query(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
            """,
            (table,),
        )
        return source.fetch_all()

    elif db_type == "oracle":
        source.execute_query(
            """
            SELECT column_name, data_type
            FROM user_tab_columns
            WHERE table_name = UPPER(:1)
            ORDER BY column_id
            """,
            (table,),
        )
        return source.fetch_all()

    else:
        raise MigrationError(f"Cannot inspect schema for db_type={db_type!r}")


def _build_create_table_sql(
    table: str,
    columns: list[tuple[str, str]],
    target_db: str,
) -> str:
    """Build a CREATE TABLE IF NOT EXISTS statement for the target database."""
    col_defs = ", ".join(
        f"{col_name} {_map_type(col_type, target_db)}" for col_name, col_type in columns
    )
    return f"CREATE TABLE IF NOT EXISTS {table} ({col_defs})"


def _build_insert_sql(
    table: str,
    column_names: list[str],
    target_db: str,
) -> str:
    """Build a parameterised INSERT statement for the target database."""
    cols = ", ".join(column_names)
    placeholder = "?" if target_db == "sqlite" else "%s"
    placeholders = ", ".join([placeholder] * len(column_names))
    return f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def migrate_table(
    source: Any,
    target: Any,
    table: str,
    create_table: bool = True,
    batch_size: int = 500,
    truncate_target: bool = False,
) -> dict[str, Any]:
    """
    Migrate a table from one database to another.

    Copies all rows from ``source`` to ``target``. Optionally creates
    the target table using best-effort type mapping from the source schema.

    Args:
        source: A connected SQLPyHelper instance (the data source).
        target: A connected SQLPyHelper instance (the destination).
        table:  Name of the table to migrate.
        create_table: If True, creates the table in the target database
                      using best-effort type mapping. If False, the table
                      must already exist in the target. Default: True.
        batch_size: Number of rows to insert per batch. Default: 500.
        truncate_target: If True, deletes all existing rows in the target
                         table before inserting. Default: False.

    Returns:
        A dict with migration statistics::

            {
                "table": "users",
                "rows_migrated": 1234,
                "batches": 3,
                "source_db": "sqlite",
                "target_db": "postgres",
            }

    Raises:
        MigrationError: If the migration fails for any reason.

    Example::

        from sqlpyhelper.db_helper import SQLPyHelper
        from sqlpyhelper.migration import migrate_table

        with SQLPyHelper(db_type="sqlite", database="local.db") as source:
            with SQLPyHelper(db_type="postgres", host="localhost",
                             user="user", password="pass",
                             database="mydb") as target:

                stats = migrate_table(
                    source=source,
                    target=target,
                    table="users",
                    create_table=True,
                    batch_size=1000,
                )
                print(f"Migrated {stats['rows_migrated']} rows")
    """
    source_db = source.db_type
    target_db = target.db_type

    logger.info(
        "Starting migration of table '%s' from %s -> %s",
        table,
        source_db,
        target_db,
    )

    try:
        # Step 1 — fetch column info from source
        columns = _get_column_info(source, table)
        if not columns:
            raise MigrationError(
                f"Table '{table}' not found in source database " f"or has no columns."
            )
        column_names = [col[0] for col in columns]
        logger.info("Found %d columns: %s", len(columns), column_names)

        # Step 2 — optionally create the table in the target
        if create_table:
            ddl = _build_create_table_sql(table, columns, target_db)
            logger.info("Creating target table: %s", ddl)
            target.execute_query(ddl)

        # Step 3 — optionally truncate the target table
        if truncate_target:
            if target_db == "sqlite":
                target.execute_query(f"DELETE FROM {table}")
            else:
                target.execute_query(f"TRUNCATE TABLE {table}")
            logger.info("Truncated target table '%s'", table)

        # Step 4 — fetch all rows from source
        source.execute_query(f"SELECT * FROM {table}")
        all_rows = source.fetch_all()
        total_rows = len(all_rows)
        logger.info("Fetched %d rows from source", total_rows)

        if total_rows == 0:
            logger.info("Source table '%s' is empty — nothing to migrate", table)
            return {
                "table": table,
                "rows_migrated": 0,
                "batches": 0,
                "source_db": source_db,
                "target_db": target_db,
            }

        # Step 5 — insert in batches
        insert_sql = _build_insert_sql(table, column_names, target_db)
        batches = 0
        for i in range(0, total_rows, batch_size):
            batch = all_rows[i : i + batch_size]
            target.cursor.executemany(insert_sql, batch)
            target.connection.commit()
            batches += 1
            logger.info(
                "Inserted batch %d (%d/%d rows)",
                batches,
                min(i + batch_size, total_rows),
                total_rows,
            )

        logger.info("Migration complete: %d rows in %d batches", total_rows, batches)

        return {
            "table": table,
            "rows_migrated": total_rows,
            "batches": batches,
            "source_db": source_db,
            "target_db": target_db,
        }

    except MigrationError:
        raise
    except Exception as e:
        raise MigrationError(f"Migration of '{table}' failed: {e}") from e
