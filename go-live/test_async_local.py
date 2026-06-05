"""
go-live/test_async_local.py
Test the async SQLPyHelper API using SQLite.
Requires: pip install "sqlpyhelper[async-sqlite]"
Run from repo root: python go-live/test_async_local.py
"""
import asyncio
import os

from sqlpyhelper.async_helper import AsyncSQLPyHelper

# Cleanup any leftover files from previous runs
if os.path.exists("test_async.db"):
    os.remove("test_async.db")


async def main():
    print("Testing async SQLite API...")

    async with AsyncSQLPyHelper(db_type="sqlite", database="test_async.db") as db:

        # Create table
        await db.execute(
            "CREATE TABLE IF NOT EXISTS products "
            "(id INTEGER, name TEXT, price REAL)"
        )
        print("✓ execute (CREATE TABLE)")

        # Single insert
        await db.execute(
            "INSERT INTO products VALUES ($1, $2, $3)", 1, "Laptop", 999.99
        )
        print("✓ execute (INSERT)")

        # Bulk insert
        await db.execute_many(
            "INSERT INTO products VALUES ($1, $2, $3)",
            [(2, "Mouse", 29.99), (3, "Keyboard", 79.99), (4, "Monitor", 399.99)],
        )
        print("✓ execute_many")

        # fetch_all
        rows = await db.fetch_all("SELECT * FROM products")
        print(f"✓ fetch_all: {rows}")
        assert len(rows) == 4, f"Expected 4 rows, got {len(rows)}"

        # fetch_one
        row = await db.fetch_one(
            "SELECT * FROM products WHERE id = $1", 1
        )
        print(f"✓ fetch_one: {row}")
        assert row is not None, "Expected a row"
        assert row[1] == "Laptop", "Expected Laptop"

        # fetch_val
        count = await db.fetch_val("SELECT COUNT(*) FROM products")
        print(f"✓ fetch_val (count): {count}")
        assert count == 4, f"Expected count 4, got {count}"

    print("✅ Async SQLite API passed")

    # Cleanup
    os.remove("test_async.db")
    print("Cleaned up test files")


asyncio.run(main())
