"""Tests for infra_mcp.server — tool wiring end to end."""

from __future__ import annotations

import os
import sqlite3
from unittest.mock import patch

import pytest

from infra_mcp import server


@pytest.fixture()
def demo_db(tmp_path, monkeypatch):
    db = tmp_path / "demo.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE jobs (id INTEGER PRIMARY KEY, name TEXT, status TEXT)")
    conn.executemany(
        "INSERT INTO jobs (name, status) VALUES (?, ?)",
        [("sim_1", "RUN"), ("sim_2", "DONE")],
    )
    conn.commit()
    conn.close()
    monkeypatch.setenv("INFRA_MCP_SQLITE_PATH", str(db))
    return db


class TestDbTools:
    def test_list_tables(self, demo_db):
        assert server.db_list_tables() == ["jobs"]

    def test_query_returns_rows(self, demo_db):
        rows = server.db_query("SELECT name, status FROM jobs ORDER BY id")
        assert rows == [
            {"name": "sim_1", "status": "RUN"},
            {"name": "sim_2", "status": "DONE"},
        ]

    def test_query_rejects_writes(self, demo_db):
        with pytest.raises(ValueError, match="SELECT"):
            server.db_query("DELETE FROM jobs")

    def test_describe_table(self, demo_db):
        cols = server.db_describe_table("jobs")
        assert [c["name"] for c in cols] == ["id", "name", "status"]


class TestLsfTools:
    def test_jobs_forwards_user(self):
        with patch.object(server, "run_lsf", return_value="out") as run:
            assert server.lsf_jobs("alice") == "out"
            _, argv = run.call_args[0]
            assert argv == ["bjobs", "-u", "alice"]

    def test_jobs_no_user(self):
        with patch.object(server, "run_lsf", return_value="out") as run:
            server.lsf_jobs("")
            _, argv = run.call_args[0]
            assert argv == ["bjobs"]

    def test_hosts(self):
        with patch.object(server, "run_lsf", return_value="hosts") as run:
            assert server.lsf_hosts() == "hosts"
            assert run.call_args[0][1] == ["lsload"]


class TestMachineTool:
    def test_machine_info(self):
        info = server.get_machine_info()
        assert info["cpu"]["logical_cores"] >= 1
