"""
go-live/test_async_postgres.py
Test the async SQLPyHelper API using PostgreSQL.
Requires: pip install "sqlpyhelper[async-postgres]"
Update DB_* credentials below before running.
Run from repo root: python go-live/test_async_postgres.py
"""
import asyncio

from sqlpyhelper.async_helper import AsyncSQLPyHelper

# ── Update these credentials ──────────────────────────────────────────────
DB_HOST = "localhost"
DB_PORT = "5433"
DB_USER = "testdb_user"
DB_PASSWORD = "p@$$w0rd"
DB_NAME = "testdb"
# ─────────────────────────────────────────────────────────────────────────


async def main():
    print("Testing async PostgreSQL API...")

    async with AsyncSQLPyHelper(
        db_type="postgres",
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    ) as db:

        # Create table
        await db.execute(
            "CREATE TABLE IF NOT EXISTS test_async_users "
            "(id SERIAL, name TEXT, created_at TIMESTAMP DEFAULT NOW())"
        )
        print("✓ execute (CREATE TABLE)")

        # Single insert
        await db.execute(
            "INSERT INTO test_async_users (name) VALUES ($1)", "Alice"
        )
        print("✓ execute (INSERT)")

        # Bulk insert
        await db.execute_many(
            "INSERT INTO test_async_users (name) VALUES ($1)",
            [("Bob",), ("Charlie",), ("David",)],
        )
        print("✓ execute_many")

        # fetch_all
        rows = await db.fetch_all("SELECT * FROM test_async_users")
        print(f"✓ fetch_all: {rows}")
        assert len(rows) == 4, f"Expected 4 rows, got {len(rows)}"

        # fetch_one
        row = await db.fetch_one(
            "SELECT * FROM test_async_users WHERE name = $1", "Alice"
        )
        print(f"✓ fetch_one: {row}")
        assert row is not None, "Expected a row"
        assert row["name"] == "Alice", "Expected Alice"

        # fetch_val
        count = await db.fetch_val("SELECT COUNT(*) FROM test_async_users")
        print(f"✓ fetch_val (count): {count}")
        assert count == 4, f"Expected count 4, got {count}"

        # Transaction rollback
        await db.begin_transaction()
        await db.execute(
            "INSERT INTO test_async_users (name) VALUES ($1)", "Eve"
        )
        await db.rollback_transaction()
        count_after = await db.fetch_val(
            "SELECT COUNT(*) FROM test_async_users"
        )
        print(f"✓ rollback: count after rollback = {count_after} (Eve should not exist)")
        assert count_after == 4, f"Expected 4 after rollback, got {count_after}"

        # Transaction commit
        await db.begin_transaction()
        await db.execute(
            "INSERT INTO test_async_users (name) VALUES ($1)", "Frank"
        )
        await db.commit_transaction()
        count_after = await db.fetch_val(
            "SELECT COUNT(*) FROM test_async_users"
        )
        print(f"✓ commit: count after commit = {count_after} (Frank should exist)")
        assert count_after == 5, f"Expected 5 after commit, got {count_after}"

        # Cleanup
        await db.execute("DROP TABLE test_async_users")
        print("✓ cleanup: table dropped")

    print("✅ Async PostgreSQL API passed")


asyncio.run(main())
