"""
go-live/test_migration_local.py
Test cross-database migration: SQLite -> SQLite.
Run from repo root: python go-live/test_migration_local.py
"""
import os

from sqlpyhelper.db_helper import SQLPyHelper
from sqlpyhelper.migration import migrate_table

# Cleanup any leftover files from previous runs
for f in ["source.db", "target.db"]:
    if os.path.exists(f):
        os.remove(f)

print("Testing migration: SQLite -> SQLite...")

# Step 1 — set up source database
with SQLPyHelper(db_type="sqlite", database="source.db") as source:
    source.create_table(
        "orders",
        {"id": "INTEGER PRIMARY KEY", "item": "TEXT", "qty": "INTEGER"},
    )
    source.insert_bulk(
        "orders",
        [
            {"id": 1, "item": "Laptop", "qty": 2},
            {"id": 2, "item": "Mouse", "qty": 5},
            {"id": 3, "item": "Keyboard", "qty": 3},
        ],
    )
    source.execute_query("SELECT * FROM orders")
    rows = source.fetch_all()
    print(f"✓ source rows: {rows}")
    assert len(rows) == 3, f"Expected 3 source rows, got {len(rows)}"

# Step 2 — migrate
with SQLPyHelper(db_type="sqlite", database="source.db") as source:
    with SQLPyHelper(db_type="sqlite", database="target.db") as target:
        stats = migrate_table(
            source=source,
            target=target,
            table="orders",
            create_table=True,
        )
        print(f"✓ migration stats: {stats}")
        assert stats["rows_migrated"] == 3, (
            f"Expected 3 migrated, got {stats['rows_migrated']}"
        )
        assert stats["source_db"] == "sqlite"
        assert stats["target_db"] == "sqlite"

# Step 3 — verify target
with SQLPyHelper(db_type="sqlite", database="target.db") as target:
    target.execute_query("SELECT * FROM orders ORDER BY id")
    rows = target.fetch_all()
    print(f"✓ target rows: {rows}")
    assert len(rows) == 3, f"Expected 3 target rows, got {len(rows)}"
    assert rows[0][1] == "Laptop", "First row item should be Laptop"
    assert rows[1][1] == "Mouse", "Second row item should be Mouse"
    assert rows[2][1] == "Keyboard", "Third row item should be Keyboard"

# Cleanup
os.remove("source.db")
os.remove("target.db")
print("✓ cleanup: test files removed")

print("✅ Migration SQLite -> SQLite passed")
