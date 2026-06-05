import click

from sqlpyhelper.automation_utils import AutomationUtils
from sqlpyhelper.db_helper import SQLPyHelper


@click.group()
def cli():
    """SQLPyHelper Command Line Interface"""
    pass


@cli.command()
@click.option("--db_type", help="Type of database (e.g., sqlite, postgres, mysql)")
@click.option("--host", help="Database host")
@click.option("--user", help="Username")
@click.option("--password", help="Password")
@click.option("--database", help="Database name or file")
@click.option("--query", required=True, help="SQL query to run")
def run_query(db_type, host, user, password, database, query):
    """Run a single SQL query and print results"""
    db = SQLPyHelper(
        db_type=db_type, host=host, user=user, password=password, database=database
    )
    results = db.execute_query(query)
    for row in results:
        click.echo(row)
    db.close()


@cli.command()
@click.option("--db_type", required=True)
@click.option("--host")
@click.option("--user")
@click.option("--password")
@click.option("--database", required=True)
def interactive_shell(db_type, host, user, password, database):
    """Launch an interactive SQL shell"""
    db = SQLPyHelper(
        db_type=db_type, host=host, user=user, password=password, database=database
    )
    click.echo("Interactive shell started. Type your SQL query or 'exit'")
    while True:
        query = input("sqlpy> ")
        if query.lower() in ("exit", "quit"):
            break
        try:
            db.execute_query(query)
            results = db.fetch_all()
            for row in results:
                click.echo(row)
        except Exception as e:
            click.echo(f"Error: {e}")
    db.close()


@cli.command()
@click.option("--target", default="local", help="Backup destination")
@click.option("--tag", default="autobackup", help="Tag for backup file naming")
@click.option("--db-type")
@click.option("--host")
@click.option("--user")
@click.option("--password")
@click.option("--database")
@click.option("--port")
def backup(target, tag, db_type, host, user, password, database, port):
    """Create a timestamped backup of the connected database."""
    utils = AutomationUtils(
        db_type=db_type,
        host=host,
        user=user,
        password=password,
        database=database,
        port=port,
    )
    utils.backup_database(target=target, tag=tag)


@cli.command()
@click.option("--file", required=True, help="Path to CSV file")
@click.option("--table", required=True, help="Destination table")
@click.option(
    "--if-exists",
    default="append",
    type=click.Choice(["append", "replace"]),
    help="What to do if table exists",
)
@click.option("--db-type")
@click.option("--host")
@click.option("--user")
@click.option("--password")
@click.option("--database")
@click.option("--port")
def load_data(file, table, if_exists, db_type, host, user, password, database, port):
    """Load data from CSV into database table."""
    utils = AutomationUtils(
        db_type=db_type,
        host=host,
        user=user,
        password=password,
        database=database,
        port=port,
    )
    utils.load_data_from_csv(file, table, if_exists=if_exists)


@cli.command()
@click.option("--table", required=True)
@click.option("--entity-column", required=True)
@click.option("--date-column", required=True)
@click.option("--db-type")
@click.option("--host")
@click.option("--user")
@click.option("--password")
@click.option("--database")
@click.option("--port")
def detect_missing_periods(
    table, entity_column, date_column, db_type, host, user, password, database, port
):
    """Flag entities with fewer than 12 months of activity."""
    utils = AutomationUtils(
        db_type=db_type,
        host=host,
        user=user,
        password=password,
        database=database,
        port=port,
    )
    results = utils.detect_missing_periods(table, entity_column, date_column)
    for row in results:
        click.echo(row)


@cli.command()
@click.option("--table", required=True)
@click.option("--value-column", required=True)
@click.option("--group-column")
@click.option("--time-column")
@click.option("--db-type")
@click.option("--host")
@click.option("--user")
@click.option("--password")
@click.option("--database")
@click.option("--port")
def aggregate(
    table,
    value_column,
    group_column,
    time_column,
    db_type,
    host,
    user,
    password,
    database,
    port,
):
    """Aggregate numeric column optionally grouped by entity and time."""
    utils = AutomationUtils(
        db_type=db_type,
        host=host,
        user=user,
        password=password,
        database=database,
        port=port,
    )
    results = utils.aggregate_column(table, value_column, group_column, time_column)
    for row in results:
        click.echo(row)


@cli.command()
@click.option("--table", required=True)
@click.option("--numeric-column", required=True)
@click.option("--threshold", default=2, type=int)
@click.option("--db-type")
@click.option("--host")
@click.option("--user")
@click.option("--password")
@click.option("--database")
@click.option("--port")
def detect_outliers(
    table, numeric_column, threshold, db_type, host, user, password, database, port
):
    """Flag rows where values deviate statistically from average."""
    utils = AutomationUtils(
        db_type=db_type,
        host=host,
        user=user,
        password=password,
        database=database,
        port=port,
    )
    results = utils.detect_outliers(table, numeric_column, threshold)
    for row in results:
        click.echo(row)


if __name__ == "__main__":
    cli()
