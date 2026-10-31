"""Tests for infra_mcp.machine."""

from infra_mcp.machine import machine_info


def test_machine_info_shape():
    info = machine_info()
    assert info["hostname"]
    assert info["cpu"]["logical_cores"] >= 1
    assert 0 <= info["cpu"]["percent"] <= 100
    assert info["memory"]["total_gb"] > 0
    assert info["disk"]["total_gb"] > 0
    assert 0 <= info["disk"]["percent"] <= 100
