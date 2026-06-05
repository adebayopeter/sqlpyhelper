"""
go-live/test_migration_postgres.py
Test cross-database migration: SQLite -> PostgreSQL.
Requires: pip install "sqlpyhelper[postgres]"
Update DB_* credentials below before running.
Run from repo root: python go-live/test_migration_postgres.py
"""
import os

from sqlpyhelper.db_helper import SQLPyHelper
from sqlpyhelper.migration import migrate_table

# ── Update these credentials ──────────────────────────────────────────────
DB_HOST = "localhost"
DB_PORT = "5433"
DB_USER = "testdb_user"
DB_PASSWORD = "p@$$w0rd"
DB_NAME = "testdb"
# ─────────────────────────────────────────────────────────────────────────

# Cleanup any leftover files from previous runs
if os.path.exists("migration_source.db"):
    os.remove("migration_source.db")

print("Testing migration: SQLite -> PostgreSQL...")

# Step 1 — set up source SQLite database
with SQLPyHelper(db_type="sqlite", database="migration_source.db") as source:
    source.create_table(
        "products",
        {
            "id": "INTEGER PRIMARY KEY",
            "name": "TEXT",
            "price": "REAL",
            "qty": "INTEGER",
        },
    )
    source.insert_bulk(
        "products",
        [
            {"id": 1, "name": "Laptop", "price": 999.99, "qty": 10},
            {"id": 2, "name": "Mouse", "price": 29.99, "qty": 50},
            {"id": 3, "name": "Keyboard", "price": 79.99, "qty": 30},
            {"id": 4, "name": "Monitor", "price": 399.99, "qty": 15},
            {"id": 5, "name": "Headphones", "price": 149.99, "qty": 25},
        ],
    )
    source.execute_query("SELECT * FROM products")
    rows = source.fetch_all()
    print(f"✓ source rows: {len(rows)} rows in SQLite")
    assert len(rows) == 5, f"Expected 5 source rows, got {len(rows)}"

# Step 2 — migrate to PostgreSQL
with SQLPyHelper(db_type="sqlite", database="migration_source.db") as source:
    with SQLPyHelper(
        db_type="postgres",
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    ) as target:
        stats = migrate_table(
            source=source,
            target=target,
            table="products",
            create_table=True,
        )
        print(f"✓ migration stats: {stats}")
        assert stats["rows_migrated"] == 5, (
            f"Expected 5 migrated, got {stats['rows_migrated']}"
        )
        assert stats["source_db"] == "sqlite"
        assert stats["target_db"] == "postgres"

# Step 3 — verify data in PostgreSQL
with SQLPyHelper(
    db_type="postgres",
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
) as target:
    target.execute_query("SELECT * FROM products ORDER BY id")
    rows = target.fetch_all()
    print(f"✓ target rows in PostgreSQL: {rows}")
    assert len(rows) == 5, f"Expected 5 rows in PostgreSQL, got {len(rows)}"
    assert rows[0][1] == "Laptop", "First row should be Laptop"
    assert rows[1][1] == "Mouse", "Second row should be Mouse"
    assert rows[4][1] == "Headphones", "Fifth row should be Headphones"

    # Cleanup
    target.execute_query("DROP TABLE products")
    print("✓ cleanup: target table dropped")

# Cleanup source
os.remove("migration_source.db")
print("✓ cleanup: source database removed")

print("✅ Migration SQLite -> PostgreSQL passed")
