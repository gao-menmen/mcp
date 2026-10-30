import os
import json
import sqlite3
import pytest

from db_mcp.config import load_config
from db_mcp.connectors.sqlite import connect, validate_sql, list_tables, describe_table, query


class TestConfig:
    def test_load_config_from_env(self, tmp_path, monkeypatch):
        cfg = tmp_path / "config.json"
        cfg.write_text(json.dumps({"sqlite": {"file_path": "test.db"}}))
        monkeypatch.setenv("MCP_CONFIG_PATH", str(cfg))
        assert load_config() == {"sqlite": {"file_path": "test.db"}}

    def test_load_config_missing_returns_empty(self, monkeypatch):
        monkeypatch.delenv("MCP_CONFIG_PATH", raising=False)
        monkeypatch.chdir(tmp_path := __import__("pathlib").Path.cwd())
        assert load_config() == {}


class TestValidateSql:
    @pytest.mark.parametrize("sql", [
        "SELECT * FROM users",
        "select id, name from users",
        "  SELECT * FROM users  ",
        "-- comment\nSELECT * FROM users",
        "/* comment */ SELECT 1",
    ])
    def test_allows_select(self, sql):
        assert validate_sql(sql) is True

    @pytest.mark.parametrize("sql", [
        "INSERT INTO users VALUES (1)",
        "UPDATE users SET name='x'",
        "DELETE FROM users",
        "DROP TABLE users",
        "CREATE TABLE x (id INT)",
        "ALTER TABLE users ADD COLUMN x INT",
        "PRAGMA table_info(users)",
    ])
    def test_rejects_non_select(self, sql):
        assert validate_sql(sql) is False


@pytest.fixture
def db_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
    conn.execute("INSERT INTO users VALUES (1, 'Alice', 'alice@example.com')")
    conn.execute("INSERT INTO users VALUES (2, 'Bob', 'bob@example.com')")
    conn.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, amount REAL)")
    yield conn
    conn.close()


class TestSqliteConnector:
    def test_list_tables(self, db_conn):
        tables = list_tables(db_conn)
        assert "users" in tables
        assert "orders" in tables

    def test_describe_table(self, db_conn):
        cols = describe_table(db_conn, "users")
        names = [c["name"] for c in cols]
        assert "id" in names
        assert "name" in names
        assert "email" in names
        assert cols[0]["type"] == "INTEGER"

    def test_query_returns_dicts(self, db_conn):
        rows = query(db_conn, "SELECT id, name FROM users ORDER BY id")
        assert rows == [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]

    def test_query_rejects_insert(self, db_conn):
        with pytest.raises(ValueError, match="Only SELECT"):
            query(db_conn, "INSERT INTO users VALUES (3, 'Eve', 'eve@example.com')")

    def test_connect_readonly(self, tmp_path):
        db_file = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_file))
        conn.execute("CREATE TABLE t (id INTEGER)")
        conn.close()

        ro_conn = connect({"file_path": str(db_file)})
        with pytest.raises(sqlite3.OperationalError):
            ro_conn.execute("CREATE TABLE x (id INTEGER)")
        ro_conn.close()
