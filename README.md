# infra-mcp

MCP server exposing three groups of tools:

- **Database** (read-only): query a SQLite database, list tables, describe tables
- **LSF**: `bjobs`, `bhosts`, `bqueues`, `lsload` — run locally on a login node or over SSH
- **Machine info**: CPU, memory, disk, hostname

## Install

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv/Scripts/python.exe fastmcp psutil pytest
```

## Configure

Set environment variables before starting:

| Variable | Default | Purpose |
|---|---|---|
| `INFRA_MCP_SQLITE_PATH` | — | Path to the SQLite file (required for db tools) |
| `INFRA_MCP_LSF_MODE` | `local` | `local` or `ssh` |
| `INFRA_MCP_LSF_SSH_HOST` | — | LSF login node hostname (ssh mode) |
| `INFRA_MCP_LSF_SSH_USER` | — | SSH user (ssh mode) |
| `INFRA_MCP_LSF_SSH_PORT` | `22` | SSH port |

## Run

```bash
python -m infra_mcp.server        # stdio transport, for MCP clients
```

## Test

```bash
python -m pytest tests/ -q
```
