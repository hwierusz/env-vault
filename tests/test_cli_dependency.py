"""Tests for env_vault.cli_dependency."""
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from env_vault.cli_dependency import dep_cmd


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def patched():
    """Patch storage and dependency module for CLI tests."""
    data = {"vars": {"FOO": "1", "BAR": "2"}, "__dependencies__": {}}
    with (
        patch("env_vault.cli_dependency.vault_exists", return_value=True),
        patch("env_vault.cli_dependency.load_vault", return_value=data),
        patch("env_vault.cli_dependency.save_vault") as mock_save,
    ):
        yield data, mock_save


def test_dep_add_success(runner, patched):
    data, mock_save = patched
    result = runner.invoke(dep_cmd, ["add", "myvault", "FOO", "BAR", "--password", "pw"])
    assert result.exit_code == 0
    assert "added" in result.output
    mock_save.assert_called_once()


def test_dep_add_missing_vault(runner):
    with patch("env_vault.cli_dependency.vault_exists", return_value=False):
        result = runner.invoke(dep_cmd, ["add", "ghost", "FOO", "BAR", "--password", "pw"])
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_dep_add_invalid_key(runner, patched):
    result = runner.invoke(dep_cmd, ["add", "myvault", "FOO", "MISSING", "--password", "pw"])
    assert result.exit_code != 0
    assert "Error" in result.output


def test_dep_remove_success(runner, patched):
    data, mock_save = patched
    # pre-seed a dependency
    data["__dependencies__"]["FOO"] = ["BAR"]
    result = runner.invoke(dep_cmd, ["remove", "myvault", "FOO", "BAR", "--password", "pw"])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_dep_remove_nonexistent(runner, patched):
    result = runner.invoke(dep_cmd, ["remove", "myvault", "FOO", "BAR", "--password", "pw"])
    assert result.exit_code != 0
    assert "Error" in result.output


def test_dep_list_shows_deps(runner, patched):
    data, _ = patched
    data["__dependencies__"]["FOO"] = ["BAR"]
    result = runner.invoke(dep_cmd, ["list", "myvault", "FOO", "--password", "pw"])
    assert result.exit_code == 0
    assert "BAR" in result.output


def test_dep_list_empty(runner, patched):
    result = runner.invoke(dep_cmd, ["list", "myvault", "FOO", "--password", "pw"])
    assert result.exit_code == 0
    assert "No dependencies" in result.output


def test_dep_order_success(runner, patched):
    result = runner.invoke(dep_cmd, ["order", "myvault", "--password", "pw"])
    assert result.exit_code == 0
    assert "FOO" in result.output
    assert "BAR" in result.output


def test_dep_order_missing_vault(runner):
    with patch("env_vault.cli_dependency.vault_exists", return_value=False):
        result = runner.invoke(dep_cmd, ["order", "ghost", "--password", "pw"])
    assert result.exit_code != 0
