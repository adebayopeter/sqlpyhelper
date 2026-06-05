# Async Support

`AsyncSQLPyHelper` provides an async-native API for use with FastAPI,
Starlette, and any `asyncio`-based application.

## Drivers used

| Database | Async driver |
|---|---|
| SQLite | `aiosqlite` |
| PostgreSQL | `asyncpg` |
| MySQL | `aiomysql` |
| SQL Server | `aioodbc` |
| Oracle | `python-oracledb` (async mode) |

## Installation

Install with async extras:

```bash
pip install sqlpyhelper[async-postgres]   # PostgreSQL
pip install sqlpyhelper[async-mysql]      # MySQL
pip install sqlpyhelper[async-sqlite]     # SQLite
pip install sqlpyhelper[async-all]        # All async drivers
```

---

## Basic usage

```python
import asyncio
from sqlpyhelper.async_helper import AsyncSQLPyHelper

async def main():
    async with AsyncSQLPyHelper(db_type="sqlite", database="my.db") as db:
        await db.execute(
            "CREATE TABLE IF NOT EXISTS users (id INTEGER, name TEXT)"
        )
        await db.execute(
            "INSERT INTO users VALUES ($1, $2)", 1, "Alice"
        )
        rows = await db.fetch_all("SELECT * FROM users")
        print(rows)

asyncio.run(main())
```

---

## Placeholders

All queries use `$1, $2, ...` style placeholders regardless of database.
`AsyncSQLPyHelper` translates them automatically to the correct style
for each driver:

| Database | Placeholder style |
|---|---|
| PostgreSQL | `$1, $2` (native) |
| SQLite | `?` |
| MySQL / SQL Server | `%s` |
| Oracle | `:1, :2` |

```python
# Write once, works on all databases
await db.execute(
    "INSERT INTO users (id, name) VALUES ($1, $2)",
    1, "Alice"
)
```

---

## FastAPI integration

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlpyhelper.async_helper import AsyncSQLPyHelper

db = AsyncSQLPyHelper(
    db_type="postgres",
    host="localhost",
    user="user",
    password="pass",
    database="mydb",
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    yield
    await db.close()

app = FastAPI(lifespan=lifespan)

@app.get("/users")
async def get_users():
    return await db.fetch_all("SELECT * FROM users")

@app.post("/users")
async def create_user(name: str):
    await db.execute(
        "INSERT INTO users (name) VALUES ($1)", name
    )
    return {"status": "created"}
```

---

## Connection pooling

For high-traffic applications, use `setup_pool()` instead of a single
connection. Supported for PostgreSQL and MySQL:

```python
from sqlpyhelper.async_helper import AsyncSQLPyHelper

db = AsyncSQLPyHelper(
    db_type="postgres",
    host="localhost",
    user="user",
    password="pass",
    database="mydb",
)

async def startup():
    await db.setup_pool(min_size=2, max_size=20)

async def shutdown():
    await db.close_pool()
```

---

## Transactions

```python
async with AsyncSQLPyHelper(db_type="sqlite", database="my.db") as db:
    await db.begin_transaction()
    try:
        await db.execute("INSERT INTO users VALUES ($1, $2)", 1, "Alice")
        await db.execute("INSERT INTO orders VALUES ($1, $2)", 1, "Laptop")
        await db.commit_transaction()
    except Exception:
        await db.rollback_transaction()
        raise
```

---

## Bulk inserts

```python
async with AsyncSQLPyHelper(db_type="postgres", ...) as db:
    await db.execute_many(
        "INSERT INTO users (id, name) VALUES ($1, $2)",
        [(1, "Alice"), (2, "Bob"), (3, "Charlie")]
    )
```

---

## API reference

```{eval-rst}
.. autoclass:: sqlpyhelper.async_helper.AsyncSQLPyHelper
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: sqlpyhelper.async_helper.AsyncConnectionError
   :members:

.. autoclass:: sqlpyhelper.async_helper.AsyncQueryError
   :members:
```
