"""Tests for env_vault.cli_group CLI commands."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from env_vault.cli_group import group_cmd
from env_vault.group import GroupError


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def patched():
    """Patch storage and group functions used by cli_group."""
    base_data = {"DB_URL": "postgres://localhost", "PORT": "5432"}

    with patch("env_vault.cli_group.vault_exists", return_value=True) as ve, \
         patch("env_vault.cli_group.load_vault", return_value=dict(base_data)) as lv, \
         patch("env_vault.cli_group.save_vault") as sv:
        yield {"vault_exists": ve, "load_vault": lv, "save_vault": sv}


def test_group_add_success(runner, patched):
    with patch("env_vault.cli_group.add_to_group") as mock_add:
        result = runner.invoke(group_cmd, ["add", "myvault", "db", "DB_URL"],
                               input="password\npassword\n")
    assert result.exit_code == 0
    assert "Added" in result.output


def test_group_add_missing_vault(runner):
    with patch("env_vault.cli_group.vault_exists", return_value=False):
        result = runner.invoke(group_cmd, ["add", "nope", "db", "DB_URL"],
                               input="password\npassword\n")
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_group_add_group_error(runner, patched):
    with patch("env_vault.cli_group.add_to_group", side_effect=GroupError("Key 'X' does not exist in the vault.")):
        result = runner.invoke(group_cmd, ["add", "myvault", "db", "X"],
                               input="password\npassword\n")
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_group_list_shows_groups(runner, patched):
    with patch("env_vault.cli_group.list_groups", return_value=["alpha", "beta"]):
        result = runner.invoke(group_cmd, ["list", "myvault"], input="password\npassword\n")
    assert result.exit_code == 0
    assert "alpha" in result.output
    assert "beta" in result.output


def test_group_list_empty(runner, patched):
    with patch("env_vault.cli_group.list_groups", return_value=[]):
        result = runner.invoke(group_cmd, ["list", "myvault"], input="password\npassword\n")
    assert result.exit_code == 0
    assert "No groups" in result.output


def test_group_show_members(runner, patched):
    with patch("env_vault.cli_group.get_vars_for_group",
               return_value={"DB_URL": "postgres://localhost"}):
        result = runner.invoke(group_cmd, ["show", "myvault", "db"],
                               input="password\npassword\n")
    assert result.exit_code == 0
    assert "DB_URL" in result.output


def test_group_delete_success(runner, patched):
    with patch("env_vault.cli_group.delete_group"):
        result = runner.invoke(group_cmd, ["delete", "myvault", "db"],
                               input="password\npassword\n")
    assert result.exit_code == 0
    assert "deleted" in result.output


def test_group_remove_success(runner, patched):
    with patch("env_vault.cli_group.remove_from_group"):
        result = runner.invoke(group_cmd, ["remove", "myvault", "db", "DB_URL"],
                               input="password\npassword\n")
    assert result.exit_code == 0
    assert "Removed" in result.output
