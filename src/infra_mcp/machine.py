"""Local machine information via psutil."""

from __future__ import annotations

import platform
import socket
from typing import Any

import psutil


def machine_info() -> dict[str, Any]:
    """Return CPU, memory, disk and identity info for the local machine."""
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/") if platform.system() != "Windows" else psutil.disk_usage("C:\\")
    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "cpu": {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "percent": psutil.cpu_percent(interval=0.1),
        },
        "memory": {
            "total_gb": round(vm.total / 1024**3, 2),
            "available_gb": round(vm.available / 1024**3, 2),
            "percent": vm.percent,
        },
        "disk": {
            "total_gb": round(disk.total / 1024**3, 2),
            "free_gb": round(disk.free / 1024**3, 2),
            "percent": disk.percent,
        },
    }
