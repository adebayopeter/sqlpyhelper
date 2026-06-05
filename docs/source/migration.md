# Cross-Database Migration

SQLPyHelper includes a `migrate_table` utility that copies a table from one
database to another — including schema creation and batched inserts.

Supported source/target combinations:

| Source | Target |
|---|---|
| SQLite | PostgreSQL, MySQL, SQL Server, Oracle |
| PostgreSQL | SQLite, MySQL, SQL Server, Oracle |
| MySQL | SQLite, PostgreSQL, SQL Server, Oracle |
| SQL Server | SQLite, PostgreSQL, MySQL, Oracle |
| Oracle | SQLite, PostgreSQL, MySQL, SQL Server |

---

## Basic usage

```python
from sqlpyhelper.db_helper import SQLPyHelper
from sqlpyhelper.migration import migrate_table

with SQLPyHelper(db_type="sqlite", database="local.db") as source:
    with SQLPyHelper(
        db_type="postgres",
        host="localhost",
        user="user",
        password="pass",
        database="mydb",
    ) as target:

        stats = migrate_table(
            source=source,
            target=target,
            table="users",
        )
        print(f"Migrated {stats['rows_migrated']} rows")
```

---

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `source` | `SQLPyHelper` | required | Connected source database instance |
| `target` | `SQLPyHelper` | required | Connected target database instance |
| `table` | `str` | required | Name of the table to migrate |
| `create_table` | `bool` | `True` | Create the table in the target using best-effort type mapping |
| `batch_size` | `int` | `500` | Number of rows inserted per batch |
| `truncate_target` | `bool` | `False` | Delete all rows in the target table before inserting |

---

## Return value

`migrate_table` returns a dictionary with migration statistics:

```python
{
    "table": "users",
    "rows_migrated": 1234,
    "batches": 3,
    "source_db": "sqlite",
    "target_db": "postgres",
}
```

---

## Examples

### SQLite → PostgreSQL (app going to production)

```python
from sqlpyhelper.db_helper import SQLPyHelper
from sqlpyhelper.migration import migrate_table

with SQLPyHelper(db_type="sqlite", database="dev.db") as source:
    with SQLPyHelper(
        db_type="postgres",
        host="prod-host",
        user="prod_user",
        password="prod_pass",
        database="prod_db",
    ) as target:
        for table in ["users", "orders", "products"]:
            stats = migrate_table(source=source, target=target, table=table)
            print(f"{table}: {stats['rows_migrated']} rows migrated")
```

### MySQL → SQL Server (database platform change)

```python
with SQLPyHelper(
    db_type="mysql", host="old-host",
    user="user", password="pass", database="legacy_db"
) as source:
    with SQLPyHelper(
        db_type="sqlserver", host="new-host",
        user="user", password="pass", database="new_db",
        driver="ODBC Driver 17 for SQL Server"
    ) as target:
        stats = migrate_table(
            source=source,
            target=target,
            table="customers",
            batch_size=1000,
            truncate_target=True,
        )
```

### Using existing target table (no auto-create)

If you have already created the target table with the exact schema you want,
set `create_table=False`:

```python
stats = migrate_table(
    source=source,
    target=target,
    table="users",
    create_table=False,
)
```

---

## Type mapping

When `create_table=True`, SQLPyHelper maps source column types to the
appropriate types for the target database:

| Generic type | SQLite | PostgreSQL | MySQL | SQL Server | Oracle |
|---|---|---|---|---|---|
| integer | INTEGER | INTEGER | INT | INT | NUMBER |
| real | REAL | DOUBLE PRECISION | DOUBLE | FLOAT | FLOAT |
| text | TEXT | TEXT | TEXT | NVARCHAR(MAX) | CLOB |
| varchar | TEXT | TEXT | VARCHAR(255) | NVARCHAR(255) | VARCHAR2(255) |
| blob | BLOB | BYTEA | BLOB | VARBINARY(MAX) | BLOB |
| bool | NUMERIC | BOOLEAN | TINYINT(1) | BIT | NUMBER(1) |
| date | TEXT | DATE | DATE | DATE | DATE |
| timestamp | TEXT | TIMESTAMP | DATETIME | DATETIME2 | TIMESTAMP |

---

## Limitations

- **Primary keys and constraints are not migrated.** The target table is
  created with plain column definitions only. Add constraints manually
  after migration if needed.
- **Indexes are not migrated.** Recreate them on the target after migration.
- **Large tables** are handled via batching (`batch_size` parameter) but
  the full result set is fetched into memory first. For very large tables
  (millions of rows), consider migrating in chunks using `truncate_target=False`
  and filtering the source query manually.
- **Oracle** requires the source table name in uppercase when using
  `user_tab_columns`.

---

## API reference

```{eval-rst}
.. autofunction:: sqlpyhelper.migration.migrate_table

.. autoclass:: sqlpyhelper.migration.MigrationError
   :members:
```