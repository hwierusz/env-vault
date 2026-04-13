"""Tests for env_vault.cli_permission."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from env_vault.cli_permission import permission_cmd


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def patched():
    with patch("env_vault.cli_permission.vault_exists", return_value=True), \
         patch("env_vault.cli_permission.load_vault") as mock_load, \
         patch("env_vault.cli_permission.save_vault") as mock_save:
        mock_load.return_value = {}
        yield mock_load, mock_save


def test_grant_success(runner, patched):
    mock_load, mock_save = patched
    result = runner.invoke(permission_cmd, ["grant", "myvault", "alice", "read"])
    assert result.exit_code == 0
    assert "Granted" in result.output
    assert "alice" in result.output


def test_grant_invalid_permission(runner, patched):
    result = runner.invoke(permission_cmd, ["grant", "myvault", "alice", "superuser"])
    assert result.exit_code != 0
    assert "Invalid permission" in result.output


def test_grant_missing_vault(runner):
    with patch("env_vault.cli_permission.vault_exists", return_value=False):
        result = runner.invoke(permission_cmd, ["grant", "ghost", "alice", "read"])
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_revoke_success(runner, patched):
    mock_load, mock_save = patched
    mock_load.return_value = {"__permissions__": {"alice": ["write"]}}
    result = runner.invoke(permission_cmd, ["revoke", "myvault", "alice", "write"])
    assert result.exit_code == 0
    assert "Revoked" in result.output


def test_revoke_missing_permission(runner, patched):
    result = runner.invoke(permission_cmd, ["revoke", "myvault", "nobody", "admin"])
    assert result.exit_code != 0
    assert "does not have" in result.output


def test_list_no_permissions(runner, patched):
    result = runner.invoke(permission_cmd, ["list", "myvault"])
    assert result.exit_code == 0
    assert "No permissions" in result.output


def test_list_with_permissions(runner, patched):
    mock_load, _ = patched
    mock_load.return_value = {"__permissions__": {"alice": ["read", "write"]}}
    result = runner.invoke(permission_cmd, ["list", "myvault"])
    assert result.exit_code == 0
    assert "alice" in result.output


def test_check_yes(runner, patched):
    mock_load, _ = patched
    mock_load.return_value = {"__permissions__": {"alice": ["read"]}}
    result = runner.invoke(permission_cmd, ["check", "myvault", "alice", "read"])
    assert result.exit_code == 0
    assert "YES" in result.output


def test_check_no(runner, patched):
    result = runner.invoke(permission_cmd, ["check", "myvault", "nobody", "admin"])
    assert result.exit_code == 0
    assert "NO" in result.output
