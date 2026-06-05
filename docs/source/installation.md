# Installation

Install the base package (includes SQLite support out of the box):

```bash
pip install sqlpyhelper
```

Install with your database driver:

```bash
pip install sqlpyhelper[postgres]    # PostgreSQL
pip install sqlpyhelper[mysql]       # MySQL
pip install sqlpyhelper[sqlserver]   # SQL Server
pip install sqlpyhelper[oracle]      # Oracle
pip install sqlpyhelper[all]         # All databases
```

## Requirements

- Python 3.8 or higher
- Database driver for your target database (installed via extras above)
