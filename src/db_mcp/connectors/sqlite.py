"""SQLite connector with read-only enforcement."""

import re
import sqlite3
from typing import Any

_ALLOWED_PATTERN = re.compile(
    r"^\s*(?:--[^\n]*\n|/\*.*?\*/\s*)*SELECT\b",
    re.IGNORECASE | re.DOTALL,
)


def connect(config: dict) -> sqlite3.Connection:
    """Open a SQLite database in read-only mode.

    Args:
        config: Dict with key "file_path" pointing to the SQLite file.

    Returns:
        A sqlite3.Connection opened read-only.
    """
    file_path = config["file_path"]
    # URI mode required for mode=ro
    uri = f"file:{file_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    return conn


def validate_sql(sql: str) -> bool:
    """Return True if the SQL is a read-only SELECT statement."""
    return bool(_ALLOWED_PATTERN.match(sql))


def list_tables(conn: sqlite3.Connection) -> list[str]:
    """Return all table names in the database."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    return [row[0] for row in cursor.fetchall()]


def describe_table(conn: sqlite3.Connection, table_name: str) -> list[dict[str, Any]]:
    """Return column info for a table as a list of dicts."""
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    columns = []
    for row in cursor.fetchall():
        columns.append(
            {
                "cid": row[0],
                "name": row[1],
                "type": row[2],
                "notnull": bool(row[3]),
                "default": row[4],
                "pk": bool(row[5]),
            }
        )
    return columns


def query(conn: sqlite3.Connection, sql: str) -> list[dict[str, Any]]:
    """Execute a SELECT query and return rows as a list of dicts.

    Raises:
        ValueError: If sql is not a SELECT statement.
    """
    if not validate_sql(sql):
        raise ValueError("Only SELECT queries are allowed.")
    cursor = conn.execute(sql)
    column_names = [description[0] for description in cursor.description]
    return [dict(zip(column_names, row)) for row in cursor.fetchall()]
