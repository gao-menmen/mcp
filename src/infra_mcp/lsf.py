"""Run LSF commands either locally or over SSH.

LSF has no usable Python SDK, so we wrap the CLI (bjobs, bhosts, lsload, ...)
the same way ops teams do. Commands always run without a shell, with a
timeout, and return trimmed text output.
"""

from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass

DEFAULT_TIMEOUT = 30
MAX_OUTPUT_CHARS = 50_000


@dataclass(frozen=True)
class LsfConfig:
    """How to reach LSF.

    mode="local": run bjobs directly (deploy on an LSF login/submit host).
    mode="ssh":   ssh to a login node and run bjobs there.
    """

    mode: str = "local"          # "local" | "ssh"
    ssh_host: str = ""           # e.g. "lsf-login.example.com"
    ssh_user: str = ""           # empty = current user
    ssh_port: int = 22
    timeout: int = DEFAULT_TIMEOUT


class LsfError(RuntimeError):
    """Raised when an LSF command fails."""


def _truncate(text: str, limit: int = MAX_OUTPUT_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [truncated, {len(text) - limit} chars omitted]"


def _build_argv(config: LsfConfig, lsf_argv: list[str]) -> list[str]:
    if config.mode == "local":
        return list(lsf_argv)
    if config.mode == "ssh":
        if not config.ssh_host:
            raise LsfError("ssh mode requires ssh_host to be set")
        target = f"{config.ssh_user}@{config.ssh_host}" if config.ssh_user else config.ssh_host
        remote_cmd = " ".join(shlex.quote(a) for a in lsf_argv)
        return [
            "ssh",
            "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=10",
            "-p", str(config.ssh_port),
            target,
            remote_cmd,
        ]
    raise LsfError(f"unknown mode: {config.mode!r}")


def run_lsf(config: LsfConfig, lsf_argv: list[str], timeout: int | None = None) -> str:
    """Run an LSF command and return stdout (trimmed).

    Raises:
        LsfError: on non-zero exit, timeout, or missing binary.
    """
    argv = _build_argv(config, lsf_argv)
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout or config.timeout,
        )
    except FileNotFoundError as exc:
        raise LsfError(f"command not found: {argv[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise LsfError(f"command timed out after {exc.timeout}s: {' '.join(argv)}") from exc

    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        raise LsfError(f"'{' '.join(argv)}' exited {proc.returncode}: {stderr}")
    return _truncate(proc.stdout.strip())
