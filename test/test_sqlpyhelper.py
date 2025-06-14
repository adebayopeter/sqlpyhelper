from sqlpyhelper.db_helper import SQLPyHelper


# SQLite Test
def test_sqlite():
    print("Testing SQLite...")
    db = SQLPyHelper()
    db.execute_query("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)")
    db.execute_query("INSERT INTO users (name) VALUES (?)", ("Alice",))
    db.execute_query("INSERT INTO users (name) VALUES (?)", ("Bob",))
    db.execute_query("SELECT * FROM users")
    results = db.fetch_all()
    print("Results:", results)
    db.close()


# PostgreSQL Test (Ensure you have PostgreSQL running locally)
def test_postgres():
    print("Testing PostgreSQL...")
    db = SQLPyHelper()
    db.execute_query("CREATE TABLE IF NOT EXISTS employees (id SERIAL PRIMARY KEY, name VARCHAR(100))")
    db.execute_query("INSERT INTO employees (name) VALUES (%s)", ("Charlie",))
    db.execute_query("SELECT * FROM employees")
    results = db.fetch_all()
    print("Results:", results)
    db.close()


# MySQL Test (Ensure MySQL is running locally)
def test_mysql():
    print("Testing MySQL...")
    db = SQLPyHelper()
    db.execute_query("CREATE TABLE IF NOT EXISTS customers (id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(100))")
    db.execute_query("INSERT INTO customers (name) VALUES (%s)", ("Joe",))
    db.execute_query("SELECT * FROM customers")
    results = db.fetch_all()
    print("Results:", results)
    db.close()


# SQL Server Test (Requires ODBC Driver for SQL Server)
def test_sqlserver():
    print("Testing SQL Server...")
    db = SQLPyHelper()
    db.execute_query("CREATE TABLE IF NOT EXISTS orders (id INT PRIMARY KEY, product VARCHAR(100))")
    db.execute_query("INSERT INTO orders (id, product) VALUES (?, ?)", (1, "Laptop"))
    db.execute_query("SELECT * FROM orders")
    results = db.fetch_all()
    print("Results:", results)
    db.close()


# Oracle Test (Ensure Oracle is installed & running)
def test_oracle():
    print("Testing Oracle...")
    db = SQLPyHelper()
    db.execute_query("CREATE TABLE employees (id NUMBER PRIMARY KEY, name VARCHAR2(100))")
    db.execute_query("INSERT INTO employees (id, name) VALUES (:1, :2)", (1, "Emily"))
    db.execute_query("SELECT * FROM employees")
    results = db.fetch_all()
    print("Results:", results)
    db.close()


# Run Tests
if __name__ == "__main__":
    # test_sqlite()
    # test_postgres()
    test_mysql()
    # test_sqlserver()
    # test_oracle()
