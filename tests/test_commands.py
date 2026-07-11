import pytest

from command_center.commands import CommandRegistry, run_vps_health_check


def test_registry_contains_safe_health_command():
    registry = CommandRegistry.default()

    command = registry.get("vps.health")

    assert command.name == "vps.health"
    assert command.dangerous is False


def test_registry_rejects_unknown_command():
    registry = CommandRegistry.default()

    with pytest.raises(KeyError):
        registry.get("missing.command")


def test_vps_health_check_returns_safe_summary():
    result = run_vps_health_check()

    assert result["ok"] is True
    assert "hostname" in result
    assert "disk_root" in result
