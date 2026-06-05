# SQLPyHelper Go-Live Tests

End-to-end tests against the installed `sqlpyhelper` package.
Run these before every PyPI release to verify the live package works correctly.

## Setup

```bash
# Install the package with all drivers
pip install --upgrade sqlpyhelper
pip install "sqlpyhelper[postgres]"
pip install "sqlpyhelper[async-sqlite]"
pip install "sqlpyhelper[async-postgres]"
```

## Running the tests

Run from the repo root in this order:

```bash
# 1. Sync API (SQLite — no database required)
python go-live/test_local.py

# 2. Async API (SQLite — no database required)
python go-live/test_async_local.py

# 3. Async API (PostgreSQL — update credentials in file first)
python go-live/test_async_postgres.py

# 4. Migration (SQLite -> SQLite — no database required)
python go-live/test_migration_local.py

# 5. Migration (SQLite -> PostgreSQL — update credentials in file first)
python go-live/test_migration_postgres.py
```

## PostgreSQL credentials

Update the `DB_*` variables at the top of these files before running:
- `test_async_postgres.py`
- `test_migration_postgres.py`

## Expected output

Each test prints `✅ ... passed` on success and cleans up after itself.
No leftover `.db` files or tables should remain after a successful run.

## Known limitations

- SQLite transaction rollback is not tested here due to SQLite's
  autocommit behaviour. This will be addressed in v0.2.0.
- MySQL, SQL Server, and Oracle tests require live databases
  and are not included in this suite yet.
