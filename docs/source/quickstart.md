# Quickstart

## Basic usage

```python
from sqlpyhelper.db_helper import SQLPyHelper

# Use as a context manager — connection closes automatically
with SQLPyHelper(db_type="sqlite", database="mydb.db") as db:
    db.create_table("users", {"id": "INTEGER PRIMARY KEY", "name": "TEXT"})
    db.execute_query("INSERT INTO users (name) VALUES (?)", ("Alice",))
    results = db.fetch_all()
    print(results)  # [(1, 'Alice')]
```

## Using environment variables

Create a `.env` file in your project root:

```bash
DB_TYPE=postgres
DB_HOST=localhost
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=your_database
```

Then initialise without arguments:

```python
from sqlpyhelper.db_helper import SQLPyHelper

db = SQLPyHelper()  # reads from .env automatically
```

## Error handling

```python
from sqlpyhelper.db_helper import SQLPyHelper, QueryError, ConnectionError

try:
    with SQLPyHelper(db_type="sqlite", database="mydb.db") as db:
        db.execute_query("SELECT * FROM nonexistent_table")
except QueryError as e:
    print(f"Query failed: {e}")
except ConnectionError as e:
    print(f"Connection failed: {e}")
```
