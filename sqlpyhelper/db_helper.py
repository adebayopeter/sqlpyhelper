import csv
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file


def log_query(query):
    """Logs queries for debugging purposes."""
    with open("query_log.txt", "a") as f:
        f.write(query + "\n")


class SQLPyHelper:
    def __init__(self):
        self.db_type = os.getenv("DB_TYPE").lower()
        self.host = os.getenv("DB_HOST")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.database = os.getenv("DB_NAME")
        self.driver = os.getenv("DB_DRIVER")
        self.oracle_sid = os.getenv("ORACLE_SID")
        self.pool = None

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
                print(f"Error executing query: {e}")

    def fetch_one(self):
        """Fetches a single row"""
        try:
            return self.cursor.fetchone()
        except Exception as e:
            print(f"Error fetching row: {e}")
            return None

    def fetch_all(self):
        """Fetches all rows from the last executed query"""
        try:
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error fetching rows: {e}")
            return None

    def fetch_by_param(self, table_name, column_name, value):
        try:
            query = f"SELECT * FROM {table_name} WHERE {column_name} = %s"
            self.cursor.execute(query, (value,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error fetching row(s): {e}")
            return None

    def close(self):
        """Closes the connection"""
        try:
            self.cursor.close()
            self.connection.close()
        except Exception as e:
            print(f"Error closing connection: {e}")
            return None

    def create_table(self, table_name, columns):
        """
        Creates a table dynamically using a dictionary format.
        Example:
        columns = {'id': 'INTEGER PRIMARY KEY', 'name': 'TEXT', 'age': 'INTEGER'}
        """
        try:
            column_defs = ", ".join(f"{col} {dtype}" for col, dtype in columns.items())
            query = f"CREATE TABLE {table_name} ({column_defs})"
            self.execute_query(query)
        except Exception as e:
            print(f"Error creating table: {e}")
            return None

    def insert_bulk(self, table_name, data):
        """
        Inserts multiple rows at once.
        Example:
        data = [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]
        """
        try:
            columns = ", ".join(data[0].keys())  # Extract column names
            placeholders = ", ".join(["%s" for _ in data[0].keys()])  # Generate placeholders
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            values = [tuple(row.values()) for row in data]
            self.cursor.executemany(query, values)
            self.connection.commit()

        except Exception as e:
            print(f"Error inserting bulk rows: {e}")
            return None

    def backup_table(self, table_name, backup_file):
        """
        Exports table data into a CSV file.
        Example:
        backup_table('users', 'users_backup.csv')
        """
        try:
            query = f"SELECT * FROM {table_name}"
            self.execute_query(query)
            rows = self.fetch_all()

            with open(backup_file, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([desc[0] for desc in self.cursor.description])  # Column headers
                writer.writerows(rows)
        except Exception as e:
            print(f"Error backing up table: {e}")
            return None

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
            print(f"⚠️ Error setting up connection pool: {e}")
            self.pool = None  # Prevent broken pool usage

    def get_connection_from_pool(self):
        """Fetches a connection from the pool."""
        return self.pool.get_connection()

    def return_connection_to_pool(self):
        """Returns a connection back to the pool."""
        self.connection.close()

    def reconnect(self):
        """Reconnects to the database if connection is lost"""
        try:
            self.connection.close()  # Close existing connection
            self.__init__()  # Reinitialize the connection
            print("Database reconnected successfully.")
        except Exception as e:
            print(f"Error during reconnection: {e}")

    def begin_transaction(self):
        self.execute_query("START TRANSACTION")

    def rollback_transaction(self):
        self.execute_query("ROLLBACK")
