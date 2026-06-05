"""
go-live/test_local.py
Test the sync SQLPyHelper API using SQLite.
Run from repo root: python go-live/test_local.py
"""
import os

from sqlpyhelper.db_helper import SQLPyHelper

# Cleanup any leftover files from previous runs
for f in ["test_local.db", "users_backup.csv"]:
    if os.path.exists(f):
        os.remove(f)

print("Testing sync API...")

with SQLPyHelper(db_type="sqlite", database="test_local.db") as db:

    # Create table
    db.create_table("users", {"id": "INTEGER PRIMARY KEY", "name": "TEXT"})
    print("✓ create_table")

    # Insert single rows
    db.execute_query("INSERT INTO users (name) VALUES (?)", ("Alice",))
    db.execute_query("INSERT INTO users (name) VALUES (?)", ("Bob",))

    # fetch_all
    db.execute_query("SELECT * FROM users")
    rows = db.fetch_all()
    print(f"✓ fetch_all: {rows}")
    assert len(rows) == 2, f"Expected 2 rows, got {len(rows)}"

    # fetch_by_param
    result = db.fetch_by_param("users", "name", "Alice")
    print(f"✓ fetch_by_param: {result}")
    assert len(result) == 1, f"Expected 1 row, got {len(result)}"
    assert result[0][1] == "Alice", "Expected Alice"

    # insert_bulk
    db.insert_bulk("users", [{"name": "Charlie"}, {"name": "David"}])
    db.execute_query("SELECT * FROM users")
    rows = db.fetch_all()
    print(f"✓ insert_bulk: {rows}")
    assert len(rows) == 4, f"Expected 4 rows, got {len(rows)}"

    # fetch_one
    db.execute_query("SELECT * FROM users WHERE name = ?", ("Bob",))
    row = db.fetch_one()
    print(f"✓ fetch_one: {row}")
    assert row is not None, "Expected a row"
    assert row[1] == "Bob", "Expected Bob"

    # insert_dynamic
    db.insert_dynamic("users", {"name": "Eve"})
    db.execute_query("SELECT * FROM users")
    rows = db.fetch_all()
    print(f"✓ insert_dynamic: {rows}")
    assert len(rows) == 5, f"Expected 5 rows, got {len(rows)}"

    # backup_table
    db.backup_table("users", "users_backup.csv")
    assert os.path.exists("users_backup.csv"), "Backup file not created"
    print("✓ backup_table: users_backup.csv created")

    # commit_transaction
    db.begin_transaction()
    db.execute_query("INSERT INTO users (name) VALUES (?)", ("Frank",))
    db.commit_transaction()
    db.execute_query("SELECT * FROM users")
    rows = db.fetch_all()
    assert len(rows) == 6, f"Expected 6 rows after commit, got {len(rows)}"
    print(f"✓ commit_transaction: {rows}")

print("✅ Sync API passed")

# Cleanup
os.remove("test_local.db")
os.remove("users_backup.csv")
print("Cleaned up test files")
