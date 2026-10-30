# Database MCP Server Design Spec

**Date:** 2026-10-30
**Topic:** MCP Server for querying MySQL, SQLite, and PBIX files

## Goal

Build a single MCP (Model Context Protocol) server that lets AI clients (Claude Desktop, Codex, VS Code, ZCode) safely query MySQL and SQLite databases, and interact with Power BI (.pbix) files in two ways: extract model metadata offline and execute DAX queries against a running Power BI Desktop instance.

## Architecture

A Python application using FastMCP, exposing tools over stdio transport. The server is split into three isolated connector modules (MySQL, SQLite, PBIX) behind a thin FastMCP tool layer. Configuration is provided via a JSON file or environment variables so users can register their data sources without touching code.

```
AI Client (Claude/Codex/VSCode/ZCode)
        |
        v stdio
+-------------------------------+
|  FastMCP Server (Python)      |
|  - mysql_connector (PyMySQL)  |
|  - sqlite_connector (sqlite3) |
|  - pbix_connector             |
|      - metadata: zip/JSON     |
|      - DAX: ADOMD.NET bridge  |
+-------------------------------+
```

## Components

### 1. MySQL Connector
- **Library:** PyMySQL
- **Safety:** Enforces read-only access by validating SQL before execution (only SELECT, SHOW, DESCRIBE, EXPLAIN allowed). Also recommends using a read-only MySQL user.
- **Tools:**
  - `mysql_list_databases()`
  - `mysql_list_tables(database: str)`
  - `mysql_describe_table(database: str, table: str)`
  - `mysql_query(sql: str)`

### 2. SQLite Connector
- **Library:** Built-in `sqlite3`
- **Safety:** Opens files in `mode=ro`. SQL validation only allows SELECT.
- **Tools:**
  - `sqlite_list_tables()`
  - `sqlite_describe_table(table: str)`
  - `sqlite_query(sql: str)`

### 3. PBIX Connector
Provides two capabilities:

**A. Metadata Extraction (offline)**
- PBIX files are ZIP archives. The model schema is stored in `DataModelSchema` (JSON) in newer Power BI Desktop versions.
- Parses JSON to extract: tables, columns, data types, measures, DAX expressions, relationships.
- If an older binary format is detected, returns a clear error telling the user to re-save the file in a newer Power BI Desktop version.
- **Tools:**
  - `pbix_get_metadata(file_path: str)` → tables/columns/measures/relationships

**B. DAX Query (online)**
- Requires the PBIX file to be open in Power BI Desktop.
- Power BI Desktop starts a local Analysis Services instance on a dynamic port (e.g., `localhost:54321`).
- Uses the official Microsoft ADOMD.NET client (`Microsoft.AnalysisServices.AdomdClient.NetCore`) via a small bridge process.
- **Bridge design:** A tiny .NET console app (or PowerShell script) that accepts a connection string and DAX query, executes it, and returns results as JSON. The Python MCP server invokes this bridge as a subprocess.
- **Port discovery:** Reads the Power BI Desktop `msmdsrv.port.txt` file from `%LOCALAPPDATA%\Microsoft\Power BI Desktop\AnalysisServicesWorkspaces` to find the active port automatically.
- **Tools:**
  - `pbix_discover_instances()` → list of running Power BI Desktop AS instances (ports)
  - `pbix_dax_query(port: int, dax: str)` → query result as JSON rows

## Data Flow

1. **Config loading:** At startup, the server reads a JSON config file (path from `MCP_CONFIG_PATH` env var or default `./config.json`) that defines named connections:
   ```json
   {
     "mysql": {"host": "...", "user": "...", "password": "...", "database": "..."},
     "sqlite": {"file_path": "..."},
     "pbix": {"default_file": "..."}
   }
   ```
2. **Tool registration:** FastMCP registers the tools listed above.
3. **Query execution:**
   - MySQL/SQLite: validate SQL → open connection → execute → return JSON rows.
   - PBIX metadata: open ZIP → parse JSON → return structured metadata.
   - PBIX DAX: find port → call bridge subprocess with ADOMD.NET → return JSON rows.

## Error Handling

- **Invalid SQL:** Return `{"error": "Only SELECT/SHOW/DESCRIBE/EXPLAIN queries are allowed."}` before touching the database.
- **Connection failure:** Return clear message with host/port and auth hints.
- **PBIX file not found:** Return file-not-found with the path attempted.
- **Power BI Desktop not running:** Return "No active Power BI Desktop instance found. Please open the PBIX file."
- **Old PBIX binary format:** Return "This PBIX uses an older binary format. Please re-save it in a recent version of Power BI Desktop."

## Testing Strategy

- **Unit tests** for each connector using Python's `unittest` or `pytest`.
- **SQLite tests:** Use in-memory databases with known schema/data.
- **MySQL tests:** Use a lightweight MySQL test container or mock PyMySQL for CI; local manual verification required.
- **PBIX metadata tests:** Include a small sample `.pbix` file (generated with Power BI Desktop) in `tests/fixtures/` and assert extracted metadata matches expected tables/measures.
- **DAX bridge tests:** Manual/integration test on a machine with Power BI Desktop open; unit tests mock the subprocess call.

## Global Constraints

- Python 3.15+
- All database access read-only (SELECT only)
- No external paid services
- Must work on Windows 11 (user's environment) with Power BI Desktop installed for DAX queries
- All tools return JSON-serializable dicts/lists
