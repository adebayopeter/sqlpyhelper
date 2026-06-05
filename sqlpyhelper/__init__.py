# Match the version in setup.py
__version__ = "0.1.6"

from sqlpyhelper.db_helper import (  # noqa: F401
    BackupError,
    ConnectionError,
    QueryError,
    SQLPyHelperError,
)
