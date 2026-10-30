# Database MCP Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single MCP server that provides read-only query access to MySQL and SQLite, extracts PBIX model metadata offline, and executes DAX queries against a running Power BI Desktop instance.

**Architecture:** Python + FastMCP over stdio. Three connector modules (MySQL, SQLite, PBIX) behind a thin tool layer. PBIX DAX queries use a small .NET bridge subprocess calling ADOMD.NET.

**Tech Stack:** Python 3.15+, FastMCP, PyMySQL, sqlite3, zipfile/json for PBIX metadata, .NET 8+ console bridge for ADOMD.NET.

**Spec:** `docs/superpowers/specs/2026-10-30-database-mcp-server-design.md`

## Global Constraints

- Python 3.15+
- All database access read-only (SELECT only)
- Must work on Windows 11 with Power BI Desktop installed for DAX queries
- All tools return JSON-serializable dicts/lists
- Use TDD: write failing tests first, then implement

---

## Task 1: Project scaffolding and SQLite connector

**Files:**
- Create: `pyproject.toml`
- Create: `src/db_mcp/__init__.py`
- Create: `src/db_mcp/config.py`
- Create: `src/db_mcp/connectors/__init__.py`
- Create: `src/db_mcp/connectors/sqlite.py`
- Create: `tests/test_sqlite.py`

**Steps:**
- [ ] Write failing test for `sqlite_list_tables` with in-memory DB
- [ ] Write failing test for `sqlite_describe_table`
- [ ] Write failing test for `sqlite_query` (SELECT allowed, INSERT rejected)
- [ ] Run tests to confirm they fail
- [ ] Create `pyproject.toml` with dependencies: fastmcp, pymysql, pytest
- [ ] Implement `config.py` to load JSON config from env var `MCP_CONFIG_PATH` or `./config.json`
- [ ] Implement `sqlite.py` with read-only connection and SQL validation
- [ ] Run tests to make them pass
- [ ] Commit

---

## Task 2: MySQL connector

**Files:**
- Create: `src/db_mcp/connectors/mysql.py`
- Create: `tests/test_mysql.py`

**Steps:**
- [ ] Write failing test for `mysql_list_databases` (mocked PyMySQL)
- [ ] Write failing test for `mysql_list_tables`
- [ ] Write failing test for `mysql_describe_table`
- [ ] Write failing test for `mysql_query` (SELECT allowed, DROP rejected)
- [ ] Run tests to confirm they fail
- [ ] Implement `mysql.py` with PyMySQL and SQL validation
- [ ] Run tests to make them pass
- [ ] Commit

---

## Task 3: PBIX metadata extraction

**Files:**
- Create: `src/db_mcp/connectors/pbix_metadata.py`
- Create: `tests/test_pbix_metadata.py`
- Create: `tests/fixtures/sample.pbix` (small test PBIX with known schema)

**Steps:**
- [ ] Write failing test for `pbix_get_metadata` extracting tables
- [ ] Write failing test for `pbix_get_metadata` extracting columns
- [ ] Write failing test for `pbix_get_metadata` extracting measures
- [ ] Write failing test for `pbix_get_metadata` extracting relationships
- [ ] Write failing test for old binary format detection
- [ ] Run tests to confirm they fail
- [ ] Implement `pbix_metadata.py` using zipfile to read DataModelSchema JSON
- [ ] Run tests to make them pass
- [ ] Commit

---

## Task 4: ADOMD.NET bridge for DAX queries

**Files:**
- Create: `bridge/DaxBridge/DaxBridge.csproj`
- Create: `bridge/DaxBridge/Program.cs`
- Create: `src/db_mcp/connectors/pbix_dax.py`
- Create: `tests/test_pbix_dax.py`

**Steps:**
- [ ] Write failing test for `pbix_discover_instances` (mock port file discovery)
- [ ] Write failing test for `pbix_dax_query` (mock bridge subprocess)
- [ ] Run tests to confirm they fail
- [ ] Create .NET 8 console project `DaxBridge` referencing `Microsoft.AnalysisServices.AdomdClient.NetCore`
- [ ] Implement `Program.cs` to accept connection string and DAX query, execute, return JSON
- [ ] Build the bridge: `dotnet build bridge/DaxBridge -c Release`
- [ ] Implement `pbix_dax.py` to discover Power BI Desktop AS port from `%LOCALAPPDATA%\Microsoft\Power BI Desktop\AnalysisServicesWorkspaces\msmdsrv.port.txt`
- [ ] Implement subprocess call to bridge with JSON output parsing
- [ ] Run tests to make them pass
- [ ] Commit

---

## Task 5: FastMCP server and tool registration

**Files:**
- Create: `src/db_mcp/server.py`
- Create: `tests/test_server.py`

**Steps:**
- [ ] Write failing test for server tool registration
- [ ] Run tests to confirm they fail
- [ ] Implement `server.py` using FastMCP to register all tools from connectors
- [ ] Add `main()` entry point for `python -m db_mcp.server`
- [ ] Run tests to make them pass
- [ ] Commit

---

## Task 6: End-to-end verification and documentation

**Files:**
- Create: `README.md`
- Create: `config.example.json`

**Steps:**
- [ ] Create `config.example.json` with sample MySQL, SQLite, PBIX configs
- [ ] Write README with setup instructions, config format, and client integration examples (Claude Desktop, Codex, VS Code, ZCode)
- [ ] Manually verify SQLite connector with a real file
- [ ] Manually verify MySQL connector (if MySQL available) or document testing steps
- [ ] Manually verify PBIX metadata extraction with a sample file
- [ ] Manually verify DAX query bridge with Power BI Desktop open
- [ ] Run full test suite: `pytest`
- [ ] Final commit
