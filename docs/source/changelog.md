# Changelog

## [0.1.5] - 2026-06-05

### Added
- Python logging module replacing unused log_query() function
- Full type annotations on all public methods
- commit_transaction() method for explicit transaction commits
- pre-commit.sh script for local code quality checks

### Changed
- Replaced deprecated cx_Oracle with python-oracledb
- begin_transaction() is now database-agnostic
- rollback_transaction() uses connection.rollback() directly

## [0.1.4] - 2026-06-04

### Security
- Fixed SQL injection vulnerability in fetch_by_param, create_table,
  insert_bulk, backup_table, and insert_dynamic
- Fixed command injection in backup_database

### Fixed
- reconnect() no longer crashes
- return_connection_to_pool() now correctly returns connections to pool
- SQLite queries now use ? placeholder throughout
- Errors now raise typed exceptions instead of being silently printed

## [0.1.3] - 2025
- Initial public release
