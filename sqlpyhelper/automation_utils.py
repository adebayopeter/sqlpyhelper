import pandas as pd
from sqlpyhelper.db_helper import SQLPyHelper
import subprocess
from datetime import datetime
import os
import shutil


class AutomationUtils:
    def __init__(self, db=None, **db_kwargs):
        """
        Optionally accepts db instance or connection parameters like:
        db_type, host, user, password, database, port, driver.
        """
        self.db = db or SQLPyHelper(**db_kwargs)

    def backup_database(self, target="local", tag="autobackup"):
        """
        Backs up the active PostgreSQL database using pg_dump.

        Args:
            target (str): Backup destination ("local" only for now).
            tag (str): Custom tag for backup file naming.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"{tag}_{timestamp}.sql"
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        filepath = os.path.join(backup_dir, filename)

        db_name = self.db.database
        user = self.db.user
        host = self.db.host or "localhost"
        port = str(self.db.port or "5432")

        try:
            if self.db.db_type == "sqlite":
                filename2 = f"{tag}_{timestamp}.db"
                sqlite_filepath = os.path.join(backup_dir, filename2)
                shutil.copy2(self.db.database, sqlite_filepath)
            else:
                print(f"📦 Backing up database to {filepath}")
                subprocess.run(
                    [
                        "pg_dump",
                        "-h", host,
                        "-p", port,
                        "-U", user,
                        db_name,
                        "-F", "c",
                        "-f", filepath,
                    ],
                    check=True,
                    shell=False,
                )
        except subprocess.CalledProcessError as e:
            print("❌ Backup failed:", e)

    def load_data_from_csv(self, file_path, table_name, if_exists="append"):
        """
        Loads a CSV file into the specified database table.

        Args:
            file_path (str): Path to the CSV file.
            table_name (str): Destination table name in the database.
            if_exists (str): 'append' or 'replace'. Default is 'append'.
        """
        df = pd.read_csv(file_path)

        if if_exists == "replace":
            self.db.execute_query(f"DROP TABLE IF EXISTS {table_name}")

        for _, row in df.iterrows():
            self.db.insert_dynamic(table_name, row.to_dict())

    def detect_missing_periods(self, table, entity_column, date_column):
        """
        Flags rows where recurring time periods (e.g. monthly) are missing per entity.

        Args:
            table (str): Table name to query.
            entity_column (str): Column representing entity ID.
            date_column (str): Column representing timestamp/date.
        """
        if self.db.db_type == 'sqlite':
            month_expr = f"strftime('%Y-%m', {date_column})"
        else:
            month_expr = f"DATE_TRUNC('month', {date_column})"
        query = f"""
        SELECT {entity_column}, COUNT(DISTINCT {month_expr}) AS recorded_months
        FROM {table}
        GROUP BY {entity_column}
        HAVING COUNT(DISTINCT {month_expr}) < 12
        """
        self.db.execute_query(query)
        return self.db.fetch_all()

    def aggregate_column(self, table, value_column, group_column=None, time_column=None):
        """
        Computes sum of any value column grouped by entity or month.

        Args:
            table (str): Table name.
            value_column (str): Numeric column to aggregate.
            group_column (str, optional): Entity or category to group by.
            time_column (str, optional): Timestamp to extract month grouping.
        """
        if self.db.db_type == 'sqlite':
            month_expr = f"strftime('%Y-%m', {time_column})"
        else:
            month_expr = f"DATE_TRUNC('month', {time_column})"

        if group_column and time_column:
            query = f"""
            SELECT {group_column}, {month_expr} AS month, SUM({value_column}) AS total
            FROM {table}
            GROUP BY {group_column}, month
            ORDER BY month
            """
        else:
            query = f"SELECT SUM({value_column}) FROM {table}"

        self.db.execute_query(query)
        return self.db.fetch_all()

    def detect_outliers(self, table, numeric_column, threshold=2):
        """
        Detects statistical outliers based on deviation from mean.

        Args:
            table (str): Table name.
            numeric_column (str): Column to analyze.
            threshold (int): Number of standard deviations from mean to flag as outlier.
        """
        query = f"""
            SELECT *, {numeric_column} 
            AS value FROM {table}
        """
        self.db.execute_query(query)
        data = pd.DataFrame(self.db.fetch_all(), columns=[desc[0] for desc in self.db.cursor.description])

        mean_val = data["value"].mean()
        std_val = data["value"].std()
        outliers = data[abs(data["value"] - mean_val) > threshold * std_val]
        return outliers.values.tolist()
