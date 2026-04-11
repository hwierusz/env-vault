"""Tests for env_vault.cli_rollback CLI commands."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from env_vault.cli_rollback import rollback_cmd
from env_vault.rollback import RollbackError


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def patched(monkeypatch):
    """Provide easy monkeypatching for rollback module functions."""
    return monkeypatch


def test_rollback_list_shows_entries(runner, patched):
    points = [
        {"index": 0, "timestamp": "2024-01-01T00:00:00", "action": "set", "key": "FOO"},
        {"index": 1, "timestamp": "2024-01-02T00:00:00", "action": "delete", "key": "FOO"},
    ]
    patched.setattr("env_vault.cli_rollback.list_rollback_points", lambda name, vault_dir: points)
    result = runner.invoke(rollback_cmd, ["list", "myvault"])
    assert result.exit_code == 0
    assert "FOO" in result.output
    assert "set" in result.output
    assert "delete" in result.output


def test_rollback_list_empty_history(runner, patched):
    patched.setattr("env_vault.cli_rollback.list_rollback_points", lambda name, vault_dir: [])
    result = runner.invoke(rollback_cmd, ["list", "myvault"])
    assert result.exit_code == 0
    assert "No history" in result.output


def test_rollback_list_error(runner, patched):
    def boom(name, vault_dir):
        raise RollbackError("history missing")

    patched.setattr("env_vault.cli_rollback.list_rollback_points", boom)
    result = runner.invoke(rollback_cmd, ["list", "myvault"])
    assert result.exit_code != 0
    assert "history missing" in result.output


def test_rollback_apply_with_yes_flag(runner, patched):
    called_with = {}

    def fake_rollback(name, index, *, load_fn, save_fn, vault_dir):
        called_with["name"] = name
        called_with["index"] = index
        return {"A": "1", "B": "2"}

    patched.setattr("env_vault.cli_rollback.rollback_to", fake_rollback)
    result = runner.invoke(rollback_cmd, ["apply", "myvault", "2", "--yes"])
    assert result.exit_code == 0
    assert "2 variable" in result.output
    assert called_with["name"] == "myvault"
    assert called_with["index"] == 2


def test_rollback_apply_prompts_without_yes(runner, patched):
    patched.setattr(
        "env_vault.cli_rollback.rollback_to",
        lambda *a, **kw: {"X": "1"},
    )
    # Simulate user confirming
    result = runner.invoke(rollback_cmd, ["apply", "myvault", "0"], input="y\n")
    assert result.exit_code == 0


def test_rollback_apply_abort_on_no(runner, patched):
    patched.setattr(
        "env_vault.cli_rollback.rollback_to",
        lambda *a, **kw: {},
    )
    result = runner.invoke(rollback_cmd, ["apply", "myvault", "0"], input="n\n")
    assert result.exit_code != 0


def test_rollback_apply_error(runner, patched):
    def boom(*a, **kw):
        raise RollbackError("index out of range")

    patched.setattr("env_vault.cli_rollback.rollback_to", boom)
    result = runner.invoke(rollback_cmd, ["apply", "myvault", "99", "--yes"])
    assert result.exit_code != 0
    assert "out of range" in result.output
