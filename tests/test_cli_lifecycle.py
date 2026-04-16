"""Tests for env_vault.cli_lifecycle."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from env_vault.cli_lifecycle import lifecycle_cmd
from env_vault.lifecycle import LifecycleEntry, LifecycleError


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def patched(tmp_path):
    entry = LifecycleEntry(
        key="API_KEY",
        state="deprecated",
        created_at="2024-01-01T00:00:00+00:00",
        updated_at="2024-06-01T00:00:00+00:00",
        note="going away",
    )
    with patch("env_vault.cli_lifecycle.vault_exists", return_value=True), \
         patch("env_vault.cli_lifecycle.set_lifecycle", return_value=entry) as mock_set, \
         patch("env_vault.cli_lifecycle.get_lifecycle", return_value=entry) as mock_get, \
         patch("env_vault.cli_lifecycle.list_lifecycle", return_value=[entry]) as mock_list, \
         patch("env_vault.cli_lifecycle.remove_lifecycle", return_value=True) as mock_rm:
        yield {
            "entry": entry,
            "set": mock_set,
            "get": mock_get,
            "list": mock_list,
            "remove": mock_rm,
        }


def test_lifecycle_set_success(runner, patched):
    result = runner.invoke(lifecycle_cmd, ["set", "myvault", "API_KEY", "deprecated"])
    assert result.exit_code == 0
    assert "deprecated" in result.output


def test_lifecycle_set_missing_vault(runner):
    with patch("env_vault.cli_lifecycle.vault_exists", return_value=False):
        result = runner.invoke(lifecycle_cmd, ["set", "missing", "KEY", "active"])
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_lifecycle_set_lifecycle_error(runner):
    with patch("env_vault.cli_lifecycle.vault_exists", return_value=True), \
         patch("env_vault.cli_lifecycle.set_lifecycle", side_effect=LifecycleError("bad state")):
        result = runner.invoke(lifecycle_cmd, ["set", "v", "KEY", "bad"])
    assert result.exit_code != 0
    assert "bad state" in result.output


def test_lifecycle_get_success(runner, patched):
    result = runner.invoke(lifecycle_cmd, ["get", "myvault", "API_KEY"])
    assert result.exit_code == 0
    assert "deprecated" in result.output
    assert "going away" in result.output


def test_lifecycle_get_no_record(runner):
    with patch("env_vault.cli_lifecycle.vault_exists", return_value=True), \
         patch("env_vault.cli_lifecycle.get_lifecycle", return_value=None):
        result = runner.invoke(lifecycle_cmd, ["get", "v", "MISSING"])
    assert result.exit_code == 0
    assert "No lifecycle record" in result.output


def test_lifecycle_list_success(runner, patched):
    result = runner.invoke(lifecycle_cmd, ["list", "myvault"])
    assert result.exit_code == 0
    assert "API_KEY" in result.output


def test_lifecycle_list_empty(runner):
    with patch("env_vault.cli_lifecycle.vault_exists", return_value=True), \
         patch("env_vault.cli_lifecycle.list_lifecycle", return_value=[]):
        result = runner.invoke(lifecycle_cmd, ["list", "v"])
    assert "No lifecycle records" in result.output


def test_lifecycle_remove_success(runner, patched):
    result = runner.invoke(lifecycle_cmd, ["remove", "myvault", "API_KEY"])
    assert result.exit_code == 0
    assert "Removed" in result.output


def test_lifecycle_remove_not_found(runner):
    with patch("env_vault.cli_lifecycle.vault_exists", return_value=True), \
         patch("env_vault.cli_lifecycle.remove_lifecycle", return_value=False):
        result = runner.invoke(lifecycle_cmd, ["remove", "v", "GHOST"])
    assert "No lifecycle record found" in result.output
