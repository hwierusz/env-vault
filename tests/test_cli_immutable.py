"""Tests for env_vault.cli_immutable."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from env_vault.cli_immutable import immutable_cmd
from env_vault.immutable import ImmutableError


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def patched():
    with patch("env_vault.cli_immutable.lock_key") as mock_lock, \
         patch("env_vault.cli_immutable.unlock_key") as mock_unlock, \
         patch("env_vault.cli_immutable.is_locked") as mock_is_locked, \
         patch("env_vault.cli_immutable.list_locked") as mock_list:
        yield {
            "lock": mock_lock,
            "unlock": mock_unlock,
            "is_locked": mock_is_locked,
            "list": mock_list,
        }


def test_lock_success(runner, patched):
    result = runner.invoke(immutable_cmd, ["lock", "myvault", "API_KEY", "--reason", "critical"])
    assert result.exit_code == 0
    assert "immutable" in result.output
    patched["lock"].assert_called_once_with("myvault", "API_KEY", reason="critical")


def test_lock_missing_key_error(runner, patched):
    patched["lock"].side_effect = ImmutableError("Key 'MISSING' does not exist")
    result = runner.invoke(immutable_cmd, ["lock", "myvault", "MISSING"])
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_unlock_success(runner, patched):
    result = runner.invoke(immutable_cmd, ["unlock", "myvault", "API_KEY"])
    assert result.exit_code == 0
    assert "mutable" in result.output


def test_unlock_not_locked_error(runner, patched):
    patched["unlock"].side_effect = ImmutableError("Key 'API_KEY' is not locked")
    result = runner.invoke(immutable_cmd, ["unlock", "myvault", "API_KEY"])
    assert result.exit_code != 0
    assert "is not locked" in result.output


def test_status_locked(runner, patched):
    patched["is_locked"].return_value = True
    result = runner.invoke(immutable_cmd, ["status", "myvault", "API_KEY"])
    assert result.exit_code == 0
    assert "LOCKED" in result.output


def test_status_mutable(runner, patched):
    patched["is_locked"].return_value = False
    result = runner.invoke(immutable_cmd, ["status", "myvault", "DEBUG"])
    assert result.exit_code == 0
    assert "mutable" in result.output


def test_list_with_entries(runner, patched):
    patched["list"].return_value = {"API_KEY": {"reason": "critical"}, "TOKEN": {"reason": ""}}
    result = runner.invoke(immutable_cmd, ["list", "myvault"])
    assert result.exit_code == 0
    assert "API_KEY" in result.output
    assert "critical" in result.output
    assert "TOKEN" in result.output


def test_list_empty(runner, patched):
    patched["list"].return_value = {}
    result = runner.invoke(immutable_cmd, ["list", "myvault"])
    assert result.exit_code == 0
    assert "No locked keys" in result.output
