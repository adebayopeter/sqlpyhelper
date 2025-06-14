import sqlite3
import psycopg2
import mysql.connector
import pyodbc
import cx_Oracle
import csv
from psycopg2 import pool
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file


class SQLPyHelper:
    def __init__(self):
        self.db_type = os.getenv("DB_TYPE").lower()
        self.host = os.getenv("DB_HOST")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.database = os.getenv("DB_NAME")
        self.driver = os.getenv("DB_DRIVER")
        self.oracle_sid = os.getenv("ORACLE_SID")

        if self.db_type == "sqlite":
            self.connection = sqlite3.connect(self.database)
        elif self.db_type == "postgres":
            self.connection = psycopg2.connect(host=self.host, user=self.user,
                                               password=self.password, dbname=self.database)
        elif self.db_type == "mysql":
            self.connection = mysql.connector.connect(host=self.host, user=self.user,
                                                      password=self.password, database=self.database)
        elif self.db_type == "sqlserver":
            self.connection = pyodbc.connect(f"DRIVER={self.driver};SERVER={self.host};DATABASE={self.database};"
                                             f"UID={self.user};PWD={self.password}")
        elif self.db_type == "oracle":
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
            print(f"Error executing query: {e}")

    def fetch_all(self):
        """Fetches all rows from the last executed query"""
        return self.cursor.fetchall()

    def close(self):
        """Closes the connection"""
        self.cursor.close()
        self.connection.close()

    def create_table(self, table_name, columns):
        """
        Creates a table dynamically using a dictionary format.
        Example:
        columns = {'id': 'INTEGER PRIMARY KEY', 'name': 'TEXT', 'age': 'INTEGER'}
        """
        column_defs = ", ".join(f"{col} {dtype}" for col, dtype in columns.items())
        query = f"CREATE TABLE {table_name} ({column_defs})"
        self.execute_query(query)

    def insert_bulk(self, table_name, data):
        """
        Inserts multiple rows at once.
        Example:
        data = [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]
        """
        columns = ", ".join(data[0].keys())  # Extract column names
        placeholders = ", ".join(["%s" for _ in data[0].keys()])  # Generate placeholders
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        values = [tuple(row.values()) for row in data]  # Convert dictionaries to tuples
        self.cursor.executemany(query, values)
        self.connection.commit()

    def log_query(self, query):
        """Logs queries for debugging purposes."""
        with open("query_log.txt", "a") as f:
            f.write(query + "\n")

    def backup_table(self, table_name, backup_file):
        """
        Exports table data into a CSV file.
        Example:
        backup_table('users', 'users_backup.csv')
        """
        query = f"SELECT * FROM {table_name}"
        self.execute_query(query)
        rows = self.fetch_all()

        with open(backup_file, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([desc[0] for desc in self.cursor.description])  # Column headers
            writer.writerows(rows)

    def setup_postgres_pool(self, min_conn=1, max_conn=5):
        """
        Creates a connection pool for PostgreSQL.
        Example:
        setup_postgres_pool(min_conn=2, max_conn=10)
        """
        self.pool = pool.SimpleConnectionPool(min_conn, max_conn,
                                              host=self.host,
                                              user=self.user,
                                              password=self.password,
                                              dbname=self.database)

    def get_connection_from_pool(self):
        """Fetches a connection from the pool."""
        return self.pool.getconn()

    def return_connection_to_pool(self, conn):
        """Returns a connection back to the pool."""
        self.pool.putconn(conn)



