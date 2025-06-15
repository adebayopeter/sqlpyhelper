# 📌 SQLPyHelper v.0.1.3 🚀

A Python library for simplified database interactions across **SQLite, PostgreSQL, MySQL, SQL Server, and Oracle**. SQLPyHelper provides an intuitive API for handling queries, connection pooling, transactions, logging, and backups efficiently.

## 📖 Table of Contents
- [🚀 Features](#-features)
- [📦 Installation](#-installation)
- [⚙️ Setup Using `.env`](#️-setup-using-env)
- [🛠 Usage Examples](#-usage-examples)
  - [SQLite Example](#sqlite-example)
  - [PostgreSQL Example](#postgresql-example)
  - [MySQL Example](#mysql-example)
  - [SQL Server Example](#sql-server-example)
  - [Oracle Example](#oracle-example)
- [📂 Project Structure](#-project-structure)
- [📌 Available Methods in SQLPyHelper](#-available-methods-in-sqlpyhelper)
- [🌍 Contributing](#-contributing)
- [☕ Support the Project](#-support-the-project)

---

## 🚀 Features in v0.1.3
✅ Unified connection pooling for multiple databases. 
✅ Automatic reconnection for lost connections. 
✅ Transaction support (BEGIN, ROLLBACK, COMMIT). 
✅ Secure parameterized queries to prevent SQL injection. 
✅ Bulk insertion & dynamic table creation. 
✅ Logging & error handling for better debugging. 
✅ CSV export & database backups.

---
## 📦 Installation
#### Install via PyPI:
```sh
pip install sqlpyhelper
```
📌 Package on PyPI: [SQLPyHelper on PyPI](https://pypi.org/project/SQLPyHelper/)

For local development:
```sh
git clone https://github.com/adebayopeter/sqlpyhelper.git
cd sqlpyhelper
pip install -r requirements.txt
```

---

## ⚙️ Setup Using `.env`
Create a `.env` file in your project root to manage database configurations securely by renaming `.env_example`.

```sh
# .env_example (Rename to .env)
DB_TYPE=postgres
DB_HOST=localhost
DB_USER=your_user
DB_PASSWORD=your_secure_password
DB_NAME=database_name
DB_DRIVER={ODBC Driver 17 for SQL Server}
ORACLE_SID=XE
ORACLE_DB_PORT=1521
```
### Loading `.env` in Code
```pycon
from dotenv import load_dotenv
import os

load_dotenv()
db_type = os.getenv("DB_TYPE")
host = os.getenv("DB_HOST")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
database = os.getenv("DB_NAME")
```
---
## 🛠 Usage Examples
### Initialize SQLPyHelper
```pycon
from sqlpyhelper.db_helper import SQLPyHelper
db = SQLPyHelper()  # Auto-detects database type based on `DB_TYPE`
```
### SQLite Example
```pycon
db.execute_query("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
db.execute_query("INSERT INTO users (name) VALUES (?)", ("Alice",))
print(db.fetch_all()) # Expected Output: [(1, 'Alice')]
db.close()
```
### PostgreSQL Example
```pycon
db.execute_query("CREATE TABLE customers (id SERIAL PRIMARY KEY, name TEXT)")
db.execute_query("INSERT INTO customers (name) VALUES (%s)", ("Bob",))
db.begin_transaction()
db.execute_query("DELETE FROM customers WHERE name=%s", ("Bob",))
db.rollback_transaction()  # Undo delete
```
### MySQL Example
```pycon 
db.execute_query("CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100))")
db.execute_query("INSERT INTO users (id, name) VALUES (%s, %s)", (1, "Alice"))
print(db.fetch_by_param("users", "id", 1))  # Expected Output: [(1, 'Alice')]
db.close()
```
### SQL Server Example
```pycon
db.execute_query("CREATE TABLE orders (order_id INT PRIMARY KEY, item NVARCHAR(100))")
db.insert_bulk("orders", [{"order_id": 1, "item": "Laptop"}, {"order_id": 2, "item": "Mouse"}])
db.backup_table("orders", "orders_backup.csv")  # Export data to CSV
```
### Oracle Example
```pycon
db.execute_query("CREATE TABLE employees (id NUMBER PRIMARY KEY, name VARCHAR2(100))")
db.execute_query("INSERT INTO employees (id, name) VALUES (:1, :2)", (1, "Charlie"))
db.setup_connection_pool(min_conn=2, max_conn=10)  # Enable pooling for better performance
conn = db.get_connection_from_pool()
db.return_connection_to_pool(conn)
```

## 📂 Project Structure
```
📦 SQLPyHelper/
├─ sqlpyhelper/
│  ├─ __init__.py
│  └─ db_helper.py
├─ tests/
│  └─ test_sqlpyhelper.py
├─ .env_example
├─ .gitignore
├─ setup.py
├─ README.md
└─ requirements.txt
```
---
## 📌 Available Methods in SQLPyHelper

| Method | Description |
|--------|-------------|
| `execute_query(query, params=None)` | Executes a SQL query with optional parameters. |
| `fetch_one()` | Retrieves a **single row** from query results. |
| `fetch_all()` | Retrieves **all rows** from query results. |
| `fetch_by_param(table, column, value)` | Fetches **rows dynamically** based on a given parameter. |
| `create_table(table_name, columns_dict)` | Creates a table dynamically with a dictionary format. |
| `insert_bulk(table, data_list)` | Inserts **multiple rows at once** efficiently. |
| `backup_table(table, backup_file.csv)` | Exports table data to **CSV format**. |
| `setup_connection_pool()` | Initializes **database connection pooling**. |
| `get_connection_from_pool()` | Fetches a connection from the pool. |
| `return_connection_to_pool(conn)` | Returns connection back to pool. |
| `begin_transaction()` | Begins an **explicit transaction**. |
| `rollback_transaction()` | Rolls back **uncommitted transactions**. |
| `close()` | Closes the database connection safely. |

---
## 🌍 Contributing
We welcome contributions from the **open-source community**! Follow these steps to contribute:

1. Fork the repo: [SQLPyHelper GitHub Repository](https://github.com/adebayopeter/sqlpyhelper)
2. Clone your fork:
   ```sh
   git clone https://github.com/adebayopeter/sqlpyhelper.git
   ```
3. Create a new branch:
   ```sh
   git checkout -b feature-new-functionality
   ```
4. Make changes, commit, and push:
   ```sh
   git commit -m "Added new feature"
   git push origin feature-new-functionality
   ```
5. Submit a Pull Request!

---
## ☕ Support the Project

If you find SQLPyHelper useful, consider buying me a coffee to support continued development! 
Donate Here: [PayPal](https://paypal.me/adebayopeter?country.x=GB&locale.x=en_GB)
---