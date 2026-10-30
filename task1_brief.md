# Task 1 Brief: Project scaffolding and SQLite connector

## Files to create
- `pyproject.toml`
- `src/db_mcp/__init__.py`
- `src/db_mcp/config.py`
- `src/db_mcp/connectors/__init__.py`
- `src/db_mcp/connectors/sqlite.py`
- `tests/test_sqlite.py`

## Requirements

### pyproject.toml
- Project name: `db-mcp`
- Requires Python >= 3.15
- Dependencies: `fastmcp`, `pymysql`
- Dev dependencies: `pytest`
- Build system: setuptools or hatchling
- Package dir: `src/`

### config.py
- Load JSON config from `MCP_CONFIG_PATH` env var, fallback to `./config.json`
- Return dict with keys `mysql`, `sqlite`, `pbix` (may be missing)
- If file missing, return empty dict

### sqlite.py
- Function `connect(config: dict)` returns sqlite3 connection opened in read-only mode (`mode=ro`)
- Function `validate_sql(sql: str)` returns True only for SELECT statements (case-insensitive, allow leading whitespace/comments)
- Function `list_tables(conn)` returns list of table names
- Function `describe_table(conn, table_name)` returns list of column info dicts
- Function `query(conn, sql)` executes SELECT and returns list of dicts (rows as column->value)

### tests/test_sqlite.py
- Use pytest
- Test validate_sql allows SELECT, rejects INSERT/UPDATE/DELETE/DROP/CREATE/ALTER
- Test list_tables with in-memory DB containing known tables
- Test describe_table with known schema
- Test query returns correct rows as dicts
- Test query rejects non-SELECT SQL

## TDD Required
Write tests first, confirm they fail, then implement to make them pass.

## Commit
After all tests pass, commit with message "Task 1: Project scaffolding and SQLite connector"
