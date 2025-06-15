import pytest
from sqlpyhelper.db_helper import SQLPyHelper
import os


# Connection test
@pytest.fixture
def db():
    """Fixture to initialize and return a database helper instance based on DB_TYPE."""
    db_type = os.getenv("DB_TYPE", "mysql")  # Default to MySQL if not set
    os.environ["DB_TYPE"] = db_type  # Ensure correct DB type is used
    db_instance = SQLPyHelper()
    yield db_instance
    db_instance.close()  # Cleanup after tests


@pytest.mark.skipif(os.getenv("DB_TYPE") != "mysql", reason="Skipping non-MySQL tests")
def test_connection(db):
    """Ensure MySQL connects successfully."""
    assert db.connection is not None, "MySQL connection failed!"


@pytest.mark.skipif(os.getenv("DB_TYPE") != "mysql", reason="Skipping non-MySQL tests")
def test_fetch_all(db):
    """Ensure fetch_all retrieves multiple rows in MySQL."""
    db.execute_query("INSERT INTO customers (name) VALUES ('Sade'), ('Rita')")
    db.execute_query("SELECT * FROM customers")
    result = db.fetch_all()
    assert len(result) >= 2, "fetch_all() failed to return expected results!"


# Query Execution & Fetching
@pytest.mark.parametrize("db_type,query", [
    ("mysql", "CREATE TABLE test_user_tbl (id INT PRIMARY KEY, name VARCHAR(100))"),
    # ("postgres", "CREATE TABLE test_user_tbl (id SERIAL PRIMARY KEY, name TEXT)"),
    # ("sqlserver", "CREATE TABLE test_user_tbl (id INT PRIMARY KEY, name NVARCHAR(100))"),
    # ("oracle", "CREATE TABLE test_user_tbl (id NUMBER PRIMARY KEY, name VARCHAR2(100))")
])
def test_query_execution(db_type, query):
    """Test table creation syntax across database variants."""
    os.environ["DB_TYPE"] = db_type
    db = SQLPyHelper()
    db.execute_query(query)
    assert True  # If no errors, test passes
    db.close()


# Parameterized Query Tests
# @pytest.mark.parametrize("db_type", ["mysql", "postgres", "sqlserver", "oracle"])
@pytest.mark.parametrize("db_type", ["mysql"])
def test_fetch_by_param(db_type):
    """Test parameterized queries for different databases."""
    os.environ["DB_TYPE"] = db_type
    db = SQLPyHelper()

    result = db.fetch_by_param("customers", "name", "David")
    assert len(result) >= 1, f"Failed to fetch record for {db_type}"
    db.close()


# Connection Pooling Validation
# @pytest.mark.parametrize("db_type", ["mysql", "postgres", "sqlserver", "oracle"])
@pytest.mark.parametrize("db_type", ["mysql"])
def test_connection_pooling(db_type):
    """Test pooling setup for different databases."""
    os.environ["DB_TYPE"] = db_type
    db = SQLPyHelper()
    db.setup_connection_pool()
    conn = db.get_connection_from_pool()
    assert conn is not None, f"Pooling failed for {db_type}"
    db.return_connection_to_pool()
    db.close()


# Transaction Management
def test_transaction_rollback(db):
    """Verify rollback restores previous state."""
    db.begin_transaction()
    db.execute_query("INSERT INTO customers (name) VALUES ('Eve')")
    db.rollback_transaction()
    result = db.fetch_by_param("customers", "name", "Eve")
    assert len(result) == 0, "Rollback did not revert changes!"


# pytest test_sqlpyhelper.py

