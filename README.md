# 📌 SQLPyHelper

A Python library for simplified database interactions across **SQLite, PostgreSQL, MySQL, SQL Server, and Oracle**. This open-source package provides an intuitive API for handling database operations efficiently.

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
- [🌍 Contributing](#-contributing)
- [☕ Support the Project](#-support-the-project)

---

## 🚀 Features
- **Unified Interface** for multiple databases  
- **Connection pooling support** for PostgreSQL  
- **Bulk insertion & dynamic table creation**  
- **Automated logging & query execution**  
- **CSV export & backup functionality**  

---
## 📦 Installation
#### Install via PyPI:
```sh
pip install sqlpyhelper
```
📌 Package on PyPI: [SQLPyHelper on PyPI](https://pypi.org/project/SQLPyHelper/)

Or, if working from source:
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
### SQLite Example
```pycon
from sqlpyhelper.db_helper import SQLPyHelper

db = SQLPyHelper()
db.execute_query("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
db.execute_query("INSERT INTO users (name) VALUES (?)", ("Alice",))
db.execute_query("SELECT * FROM users")
print(db.fetch_all())
db.close()
```
### PostgreSQL Example
```pycon
db = SQLPyHelper()
db.execute_query("CREATE TABLE IF NOT EXISTS employees (id SERIAL PRIMARY KEY, name VARCHAR(100))")
db.execute_query("INSERT INTO employees (name) VALUES (%s)", ("Charlie",))
db.execute_query("SELECT * FROM employees")
print(db.fetch_all())
db.close()
```
### MySQL Example
```pycon
db = SQLPyHelper()
db.execute_query("CREATE TABLE IF NOT EXISTS customers (id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(100))")
db.execute_query("INSERT INTO customers (name) VALUES (%s)", ("David",))
db.execute_query("SELECT * FROM customers")
print(db.fetch_all())
db.close()
```
```pycon
db = SQLPyHelper()

# Fetch rows where customer_id = 3
customers = db.fetch_by_param("customers", "id", 3)
print(customers)

db.close()
```

### SQL Server Example
```pycon
db = SQLPyHelper()
db.execute_query("CREATE TABLE IF NOT EXISTS orders (id INT PRIMARY KEY, product VARCHAR(100))")
db.execute_query("INSERT INTO orders (id, product) VALUES (?, ?)", (1, "Laptop"))
db.execute_query("SELECT * FROM orders")
print(db.fetch_all())
db.close()
```
### Oracle Example
```pycon
db = SQLPyHelper()
db.execute_query("CREATE TABLE employees (id NUMBER PRIMARY KEY, name VARCHAR2(100))")
db.execute_query("INSERT INTO employees (id, name) VALUES (:1, :2)", (1, "Emily"))
db.execute_query("SELECT * FROM employees")
print(db.fetch_all())
db.close()
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