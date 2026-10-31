"""Tests for infra_mcp.lsf — LSF command runner."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

import pytest

from infra_mcp.lsf import LsfConfig, LsfError, _build_argv, _truncate, run_lsf


def _completed(stdout: str = "ok\n", stderr: str = "", rc: int = 0):
    return subprocess.CompletedProcess(args=[], returncode=rc, stdout=stdout, stderr=stderr)


class TestBuildArgv:
    def test_local_mode_passthrough(self):
        cfg = LsfConfig(mode="local")
        assert _build_argv(cfg, ["bjobs", "-u", "alice"]) == ["bjobs", "-u", "alice"]

    def test_ssh_mode_wraps_command(self):
        cfg = LsfConfig(mode="ssh", ssh_host="lsf-login", ssh_user="bob", ssh_port=2222)
        argv = _build_argv(cfg, ["bjobs", "-u", "all"])
        assert argv[0] == "ssh"
        assert "-p" in argv and "2222" in argv
        assert "bob@lsf-login" in argv
        # remote command is the last argument, quoted so the remote shell parses it
        assert argv[-1] == "bjobs -u all"

    def test_ssh_mode_requires_host(self):
        cfg = LsfConfig(mode="ssh", ssh_host="")
        with pytest.raises(LsfError, match="ssh_host"):
            _build_argv(cfg, ["bjobs"])

    def test_unknown_mode_rejected(self):
        with pytest.raises(LsfError, match="unknown mode"):
            _build_argv(LsfConfig(mode="wat"), ["bjobs"])

    def test_ssh_quotes_special_chars(self):
        cfg = LsfConfig(mode="ssh", ssh_host="h")
        argv = _build_argv(cfg, ["bjobs", "-J", "my job; rm -rf /"])
        # shlex.quote must neutralise the spaces/semicolon
        assert ";" not in argv[-1] or "'" in argv[-1]


class TestTruncate:
    def test_short_text_unchanged(self):
        assert _truncate("hello") == "hello"

    def test_long_text_truncated_with_note(self):
        out = _truncate("x" * 100, limit=10)
        assert out.startswith("x" * 10)
        assert "truncated" in out


class TestRunLsf:
    def test_returns_stdout_on_success(self):
        with patch("infra_mcp.lsf.subprocess.run", return_value=_completed("JOBID 123\n")):
            assert run_lsf(LsfConfig(), ["bjobs"]) == "JOBID 123"

    def test_nonzero_exit_raises_with_stderr(self):
        with patch("infra_mcp.lsf.subprocess.run",
                   return_value=_completed("", stderr="no such job", rc=1)):
            with pytest.raises(LsfError, match="no such job"):
                run_lsf(LsfConfig(), ["bjobs", "999"])

    def test_missing_binary_raises(self):
        with patch("infra_mcp.lsf.subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(LsfError, match="command not found"):
                run_lsf(LsfConfig(), ["bjobs"])

    def test_timeout_raises(self):
        with patch("infra_mcp.lsf.subprocess.run",
                   side_effect=subprocess.TimeoutExpired(cmd="bjobs", timeout=30)):
            with pytest.raises(LsfError, match="timed out"):
                run_lsf(LsfConfig(), ["bjobs"])
