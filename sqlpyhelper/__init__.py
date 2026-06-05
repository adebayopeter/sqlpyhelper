# Match the version in setup.py
__version__ = "0.1.7"

from sqlpyhelper.db_helper import (  # noqa: F401
    BackupError,
    ConnectionError,
    QueryError,
    SQLPyHelperError,
)
from sqlpyhelper.migration import MigrationError  # noqa: F401
