"""Tests for env_vault.cli_namespace."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from env_vault.cli_namespace import namespace_cmd
from env_vault.namespace import NAMESPACE_KEY, NamespaceError

BASE_DATA = {"DB_URL": "postgres://localhost", "PORT": "5432", NAMESPACE_KEY: {"database": ["DB_URL"]}}
PASSWORD = "secret"


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def patched():
    with patch("env_vault.cli_namespace.load_vault") as mock_load, \
         patch("env_vault.cli_namespace.save_vault") as mock_save:
        mock_load.return_value = dict(BASE_DATA)
        yield mock_load, mock_save


def test_ns_assign_success(runner, patched):
    mock_load, mock_save = patched
    result = runner.invoke(
        namespace_cmd, ["assign", "myvault", "PORT", "network"],
        input=f"{PASSWORD}\n{PASSWORD}\n",
    )
    assert result.exit_code == 0
    assert "Assigned" in result.output


def test_ns_assign_missing_key(runner, patched):
    mock_load, _ = patched
    mock_load.return_value = {"PORT": "5432", NAMESPACE_KEY: {}}
    result = runner.invoke(
        namespace_cmd, ["assign", "myvault", "GHOST", "ns"],
        input=f"{PASSWORD}\n{PASSWORD}\n",
    )
    assert result.exit_code == 1
    assert "Error" in result.output


def test_ns_assign_saves_vault(runner, patched):
    """Ensure save_vault is called after a successful assign."""
    mock_load, mock_save = patched
    runner.invoke(
        namespace_cmd, ["assign", "myvault", "PORT", "network"],
        input=f"{PASSWORD}\n{PASSWORD}\n",
    )
    mock_save.assert_called_once()


def test_ns_remove_success(runner, patched):
    result = runner.invoke(
        namespace_cmd, ["remove", "myvault", "DB_URL", "database"],
        input=f"{PASSWORD}\n{PASSWORD}\n",
    )
    assert result.exit_code == 0
    assert "Removed" in result.output


def test_ns_list_output(runner, patched):
    result = runner.invoke(
        namespace_cmd, ["list", "myvault"],
        input=f"{PASSWORD}\n{PASSWORD}\n",
    )
    assert result.exit_code == 0
    assert "database" in result.output


def test_ns_list_empty(runner, patched):
    mock_load, _ = patched
    mock_load.return_value = {"PORT": "5432"}
    result = runner.invoke(
        namespace_cmd, ["list", "myvault"],
        input=f"{PASSWORD}\n{PASSWORD}\n",
    )
    assert result.exit_code == 0
    assert "No namespaces" in result.output


def test_ns_show_output(runner, patched):
    result = runner.invoke(
        namespace_cmd, ["show", "myvault", "database"],
        input=f"{PASSWORD}\n{PASSWORD}\n",
    )
    assert result.exit_code == 0
    assert "DB_URL" in result.output


def test_ns_show_unknown_namespace(runner, patched):
    result = runner.invoke(
        namespace_cmd, ["show", "myvault", "nonexistent"],
        input=f"{PASSWORD}\n{PASSWORD}\n",
    )
    assert result.exit_code == 1
    assert "Error" in result.output
