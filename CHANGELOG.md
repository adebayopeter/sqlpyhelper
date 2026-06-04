# 📜 SQLPyHelper Changelog

All notable changes to this project will be documented in this file.

## [0.1.4] - 2026-06-04

### Security
- Fixed SQL injection vulnerability in `fetch_by_param`, `create_table`,
  `insert_bulk`, `backup_table`, and `insert_dynamic` — table and column
  names are now validated against a strict identifier allowlist
- Fixed command injection in `backup_database` — replaced `shell=True`
  subprocess call with list-form arguments

### Fixed
- `reconnect()` no longer crashes — original connection parameters are
  stored and replayed via `_init_kwargs`
- `return_connection_to_pool()` now correctly returns connections to the
  pool instead of closing them
- SQLite queries now use `?` placeholder instead of `%s` throughout
- Errors now raise typed exceptions (`QueryError`, `ConnectionError`,
  `BackupError`) instead of being silently printed and returning `None`

### Changed
- Development status updated to Beta (was incorrectly marked Production/Stable)

## [0.1.3] - 2025-06-16  
### **🚀 Major Enhancements & Stability Improvements**  
🔹 **Connection Pooling**  
- Unified connection pooling for **MySQL, PostgreSQL, SQL Server, and Oracle**.  
- Added **automatic reconnection handling** for lost connections.  
- Implemented **fallback to direct connection** if pooling fails.  

🔹 **Database Operations**  
- **Transaction management added** (`BEGIN`, `ROLLBACK`, `COMMIT`).  
- Improved **bulk insert handling** for safer execution.  
- Enhanced **parameterized query handling** across databases.  
- Optimized error handling with **better logging**.  

🔹 **Bug Fixes**  
- **Fixed MySQL pooling issue** (`getconn()` → `get_connection()`).  
- Resolved **PostgreSQL authentication failure**.  
- Addressed **Oracle Instant Client missing error (`DPI-1047`)**.  
- Fixed **MySQL rollback inconsistencies**, enforcing `InnoDB`.  

🔹 **Testing & Documentation Updates**  
- Added **database-specific unit tests** (`pytest`).  
- Enhanced `.env` handling for **dynamic testing**.  
- **Revamped `README.md`** with examples for all databases.  

🚀 **SQLPyHelper is now more robust, scalable, and production-ready!** 🎯 

## [0.1.2] - 2025-06-14  
### Added  
- Implemented `fetch_one()` for retrieving a single row.  
- Introduced `fetch_by_param()` for fetching rows dynamically based on parameters.  

### Fixed  
- Resolved dependency management issues for better compatibility with MySQL, PostgreSQL, and other databases.  

### Changed  
- Updated PyPI classifiers for improved visibility in search results.  

## [0.1.1] - 2025-06-12  
### Added  
- Initial public release of SQLPyHelper on PyPI.  
- Core functionalities for database interactions, including `execute_query()` and `fetch_all()`.  

---