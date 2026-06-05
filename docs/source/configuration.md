# Configuration

## Environment variables

| Variable | Description | Default |
|---|---|---|
| `DB_TYPE` | Database type: `sqlite`, `postgres`, `mysql`, `sqlserver`, `oracle` | Required |
| `DB_HOST` | Database host | `None` |
| `DB_USER` | Database user | `None` |
| `DB_PASSWORD` | Database password | `None` |
| `DB_NAME` | Database name or SQLite file path | Required |
| `DB_DRIVER` | ODBC driver name (SQL Server only) | `None` |
| `DB_PORT` | Database port | Driver default |
| `ORACLE_SID` | Oracle SID | `None` |
| `ORACLE_DB_PORT` | Oracle port | `1521` |

## Constructor parameters

All environment variables can be overridden by passing parameters directly:

```python
db = SQLPyHelper(
    db_type="postgres",
    host="localhost",
    user="myuser",
    password="mypassword",
    database="mydb",
    port="5432",
)
```
