import csv
from dotenv import load_dotenv
import os
import re

load_dotenv()  # Load environment variables from .env file


def _validate_identifier(name: str) -> str:
    """
    Validate a SQL identifier (table or column name).
    Allows only alphanumeric characters and underscores.
    Raises ValueError for anything else, preventing SQL injection via identifiers.
    """
    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', name):
        raise ValueError(
            f"Invalid SQL identifier: {name!r}. "
            "Only letters, digits, and underscores are allowed."
        )
    return name


class SQLPyHelperError(Exception):
    """Base exception for SQLPyHelper errors."""


class ConnectionError(SQLPyHelperError):
    """Raised when a database connection fails."""


class QueryError(SQLPyHelperError):
    """Raised when a query fails to execute."""


class BackupError(SQLPyHelperError):
    """Raised when a backup operation fails."""


class SQLPyHelper:
    def __init__(self, db_type=None, host=None, user=None, password=None,
                 database=None, driver=None, port=None, oracle_sid=None):

        # Store original params so reconnect() can replay them
        self._init_kwargs = {
            "db_type": db_type,
            "host": host,
            "user": user,
            "password": password,
            "database": database,
            "driver": driver,
            "port": port,
            "oracle_sid": oracle_sid,
        }

        self.db_type = db_type or os.getenv("DB_TYPE").lower()
        self.host = host or os.getenv("DB_HOST")
        self.user = user or os.getenv("DB_USER")
        self.password = password or os.getenv("DB_PASSWORD")
        self.database = database or os.getenv("DB_NAME")
        self.driver = driver or os.getenv("DB_DRIVER")
        self.port = port or os.getenv("DB_PORT")
        self.oracle_sid = oracle_sid or os.getenv("ORACLE_SID")
        self.pool = None

        if not self.db_type or not self.database:
            raise ValueError("Missing required database configuration.")

        if self.db_type == "sqlite":
            import sqlite3
            self.connection = sqlite3.connect(self.database)
        elif self.db_type == "postgres":
            import psycopg2
            self.connection = psycopg2.connect(host=self.host, user=self.user,
                                               password=self.password, dbname=self.database)
        elif self.db_type == "mysql":
            import mysql.connector
            self.connection = mysql.connector.connect(host=self.host, user=self.user,
                                                      password=self.password, database=self.database)
        elif self.db_type == "sqlserver":
            import pyodbc
            self.connection = pyodbc.connect(f"DRIVER={self.driver};SERVER={self.host};DATABASE={self.database};"
                                             f"UID={self.user};PWD={self.password}")
        elif self.db_type == "oracle":
            import cx_Oracle
            oracle_port = os.getenv("ORACLE_DB_PORT", "1521")  # Default to 1521 if not set
            dsn = cx_Oracle.makedsn(self.host, oracle_port, self.oracle_sid)
            self.connection = cx_Oracle.connect(self.user, self.password, dsn)
        else:
            raise ValueError("Unsupported database type")

        self.cursor = self.connection.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def execute_query(self, query, params=None):
        """Executes a query with optional parameters"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.connection.commit()
        except Exception as e:
            if "server has gone away" in str(e):  # Example check for MySQL lost connection
                self.reconnect()
                self.cursor.execute(query, params)
                self.connection.commit()
            else:
                raise QueryError(f"Query failed: {e}") from e

    def fetch_one(self):
        """Fetches a single row"""
        try:
            return self.cursor.fetchone()
        except Exception as e:
            raise QueryError(f"Failed to fetch row: {e}") from e

    def fetch_all(self):
        """Fetches all rows from the last executed query"""
        try:
            return self.cursor.fetchall()
        except Exception as e:
            raise QueryError(f"Failed to fetch rows: {e}") from e

    def fetch_by_param(self, table_name, column_name, value):
        try:
            table_name = _validate_identifier(table_name)
            column_name = _validate_identifier(column_name)
            placeholder = "?" if self.db_type == "sqlite" else "%s"
            query = f"SELECT * FROM {table_name} WHERE {column_name} = {placeholder}"
            self.cursor.execute(query, (value,))
            return self.cursor.fetchall()
        except Exception as e:
            raise QueryError(f"Failed to fetch by param: {e}") from e

    def close(self):
        """Closes the connection"""
        try:
            self.cursor.close()
            self.connection.close()
        except Exception as e:
            raise ConnectionError(f"Failed to close connection: {e}") from e

    def create_table(self, table_name, columns):
        """
        Creates a table dynamically using a dictionary format.
        Example:
        columns = {'id': 'INTEGER PRIMARY KEY', 'name': 'TEXT', 'age': 'INTEGER'}
        """
        try:
            table_name = _validate_identifier(table_name)
            validated_cols = {_validate_identifier(col): dtype for col, dtype in columns.items()}
            columns_def = ", ".join([f"{col} {dtype}" for col, dtype in validated_cols.items()])
            query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_def})"
            self.execute_query(query)
        except Exception as e:
            raise QueryError(f"Failed to create table: {e}") from e

    def insert_bulk(self, table_name, data):
        """
        Inserts multiple rows at once.
        Example:
        data = [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]
        """
        try:
            table_name = _validate_identifier(table_name)
            col_names = [_validate_identifier(col) for col in data[0].keys()]
            columns = ", ".join(col_names)
            placeholder = "?" if self.db_type == "sqlite" else "%s"
            placeholders = ", ".join([placeholder] * len(data[0]))
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            values = [tuple(row.values()) for row in data]
            self.cursor.executemany(query, values)
            self.connection.commit()

        except Exception as e:
            raise QueryError(f"Failed to insert bulk rows: {e}") from e

    def backup_table(self, table_name, backup_file):
        """
        Exports table data into a CSV file.
        Example:
        backup_table('users', 'users_backup.csv')
        """
        try:
            table_name = _validate_identifier(table_name)
            query = f"SELECT * FROM {table_name}"
            self.execute_query(query)
            rows = self.fetch_all()

            with open(backup_file, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([desc[0] for desc in self.cursor.description])  # Column headers
                writer.writerows(rows)
        except Exception as e:
            raise BackupError(f"Failed to backup table: {e}") from e

    def setup_connection_pool(self, min_conn=1, max_conn=5, pool_size=5):
        """Sets up connection pooling based on the database type"""
        try:
            if self.db_type == "postgres":
                from psycopg2 import pool
                self.pool = pool.SimpleConnectionPool(min_conn, max_conn,
                                                      host=self.host, user=self.user,
                                                      password=self.password, dbname=self.database)

            elif self.db_type == "mysql":
                import mysql.connector.pooling
                self.pool = mysql.connector.pooling.MySQLConnectionPool(pool_name="mypool",
                                                                        pool_size=pool_size, host=self.host,
                                                                        user=self.user, password=self.password,
                                                                        database=self.database)

            elif self.db_type == "sqlserver":
                import pyodbc
                self.pool = [
                    pyodbc.connect(f"DRIVER={self.driver};SERVER={self.host};DATABASE={self.database};"
                                   f"UID={self.user};PWD={self.password};ConnectionPooling=Yes")
                    for _ in range(pool_size)
                ]

            elif self.db_type == "oracle":
                import cx_Oracle
                oracle_port = os.getenv("ORACLE_DB_PORT", "1521")  # Default Oracle port
                dsn = cx_Oracle.makedsn(self.host, oracle_port, self.oracle_sid)
                self.pool = cx_Oracle.SessionPool(user=self.user, password=self.password, dsn=dsn,
                                                  min=min_conn, max=max_conn, increment=1, threaded=True)

            else:
                raise ValueError(f"Connection pooling not supported for {self.db_type}")
        except Exception as e:
            raise ConnectionError(f"Failed to set up connection pool: {e}") from e

    def get_connection_from_pool(self):
        """Fetches a connection from the pool."""
        return self.pool.get_connection()

    def return_connection_to_pool(self, connection=None) -> None:
        """Returns a connection back to the pool."""
        conn = connection or self.connection
        if self.pool is None:
            raise RuntimeError("No connection pool initialised. Call setup_connection_pool() first.")

        if self.db_type == "postgres":
            self.pool.putconn(conn)
        elif self.db_type == "mysql":
            conn.close()
        elif self.db_type == "oracle":
            self.pool.release(conn)
        else:
            conn.close()

    def reconnect(self):
        """Reconnects to the database if connection is lost"""
        try:
            self.connection.close()
            self.__init__(**self._init_kwargs)
            print("Database reconnected successfully.")
        except Exception as e:
            raise ConnectionError(f"Reconnection failed: {e}") from e

    def begin_transaction(self):
        self.execute_query("START TRANSACTION")

    def rollback_transaction(self):
        self.execute_query("ROLLBACK")

    def insert_dynamic(self, table, data: dict):
        """
        Dynamically constructs and executes an INSERT query with database-specific placeholders.
        """
        table = _validate_identifier(table)
        columns = ", ".join(_validate_identifier(col) for col in data.keys())
        placeholders_style = "?" if self.db_type == "sqlite" else "%s"
        placeholders = ", ".join([placeholders_style] * len(data))
        values = tuple(data.values())

        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        self.execute_query(sql, values)
