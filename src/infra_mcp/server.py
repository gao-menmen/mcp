"""infra-mcp server entry point.

Exposes three groups of tools:
  - database (read-only, reuses db_mcp.connectors.sqlite)
  - LSF cluster info (bjobs / bhosts / bqueues / lsload, locally or over SSH)
  - local machine info (CPU / memory / disk)

Run:  python -m infra_mcp.server
"""

from __future__ import annotations

import os
from typing import Any

from fastmcp import FastMCP

from infra_mcp.lsf import LsfConfig, LsfError, run_lsf
from infra_mcp.machine import machine_info

# Reuse the existing, tested SQLite read-only connector from db_mcp.
from db_mcp.connectors.sqlite import connect as sqlite_connect
from db_mcp.connectors.sqlite import describe_table, list_tables, query

mcp = FastMCP("infra-mcp")


# ---------------------------------------------------------------- database
def _db_config() -> dict:
    path = os.environ.get("INFRA_MCP_SQLITE_PATH")
    if not path:
        raise RuntimeError("Set INFRA_MCP_SQLITE_PATH to the SQLite file path.")
    return {"file_path": path}


@mcp.tool()
def db_query(sql: str) -> list[dict[str, Any]]:
    """Run a read-only SELECT query against the configured SQLite database."""
    conn = sqlite_connect(_db_config())
    try:
        return query(conn, sql)
    finally:
        conn.close()


@mcp.tool()
def db_list_tables() -> list[str]:
    """List all tables in the configured SQLite database."""
    conn = sqlite_connect(_db_config())
    try:
        return list_tables(conn)
    finally:
        conn.close()


@mcp.tool()
def db_describe_table(table_name: str) -> list[dict[str, Any]]:
    """Show columns for a table in the configured SQLite database."""
    conn = sqlite_connect(_db_config())
    try:
        return describe_table(conn, table_name)
    finally:
        conn.close()


# ---------------------------------------------------------------------- LSF
def _lsf_config() -> LsfConfig:
    mode = os.environ.get("INFRA_MCP_LSF_MODE", "local")
    return LsfConfig(
        mode=mode,
        ssh_host=os.environ.get("INFRA_MCP_LSF_SSH_HOST", ""),
        ssh_user=os.environ.get("INFRA_MCP_LSF_SSH_USER", ""),
        ssh_port=int(os.environ.get("INFRA_MCP_LSF_SSH_PORT", "22")),
    )


@mcp.tool()
def lsf_jobs(user: str = "") -> str:
    """Show LSF jobs (bjobs). Optionally filter by user, e.g. 'alice' or 'all'."""
    argv = ["bjobs", "-u", user] if user else ["bjobs"]
    return run_lsf(_lsf_config(), argv)


@mcp.tool()
def lsf_hosts() -> str:
    """Show LSF host load (lsload)."""
    return run_lsf(_lsf_config(), ["lsload"])


@mcp.tool()
def lsf_queues() -> str:
    """Show LSF queues (bqueues)."""
    return run_lsf(_lsf_config(), ["bqueues"])


@mcp.tool()
def lsf_cluster_hosts() -> str:
    """Show LSF cluster hosts and status (bhosts)."""
    return run_lsf(_lsf_config(), ["bhosts"])


# ------------------------------------------------------------------ machine
@mcp.tool()
def get_machine_info() -> dict[str, Any]:
    """Local machine CPU, memory, disk, hostname and platform."""
    return machine_info()


if __name__ == "__main__":
    mcp.run()
