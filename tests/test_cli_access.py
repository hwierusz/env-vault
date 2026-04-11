"""Tests for env_vault.cli_access CLI commands."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from env_vault.cli_access import access_cmd


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def patched():
    """Patch storage so no real files are touched."""
    acl_store = {}

    def fake_load(vault_name):
        return dict(acl_store)

    def fake_save(vault_name, data):
        acl_store.clear()
        acl_store.update(data)

    with patch("env_vault.cli_access.load_vault", side_effect=fake_load), \
         patch("env_vault.cli_access.save_vault", side_effect=fake_save):
        yield acl_store


def test_grant_success(runner, patched):
    result = runner.invoke(access_cmd, ["grant", "myapp", "alice", "-p", "read"])
    assert result.exit_code == 0
    assert "Granted" in result.output
    assert "alice" in result.output


def test_grant_invalid_permission_shows_error(runner, patched):
    result = runner.invoke(access_cmd, ["grant", "myapp", "alice", "-p", "delete"])
    assert result.exit_code != 0
    assert "Error" in result.output


def test_revoke_success(runner, patched):
    # First grant
    runner.invoke(access_cmd, ["grant", "myapp", "alice", "-p", "read", "-p", "write"])
    result = runner.invoke(access_cmd, ["revoke", "myapp", "alice", "-p", "write"])
    assert result.exit_code == 0
    assert "Revoked" in result.output


def test_revoke_unknown_user_shows_error(runner, patched):
    result = runner.invoke(access_cmd, ["revoke", "myapp", "ghost"])
    assert result.exit_code != 0
    assert "Error" in result.output


def test_list_empty_vault(runner, patched):
    result = runner.invoke(access_cmd, ["list", "myapp"])
    assert result.exit_code == 0
    assert "open" in result.output


def test_list_shows_users(runner, patched):
    runner.invoke(access_cmd, ["grant", "myapp", "alice", "-p", "admin"])
    result = runner.invoke(access_cmd, ["list", "myapp"])
    assert result.exit_code == 0
    assert "alice" in result.output
    assert "admin" in result.output


def test_check_open_vault_granted(runner, patched, monkeypatch):
    result = runner.invoke(access_cmd, ["check", "myapp", "write"])
    assert result.exit_code == 0
    assert "granted" in result.output.lower()


def test_check_denied(runner, patched, monkeypatch):
    monkeypatch.setattr("env_vault.access.getpass.getuser", lambda: "nobody")
    runner.invoke(access_cmd, ["grant", "myapp", "alice", "-p", "read"])
    result = runner.invoke(access_cmd, ["check", "myapp", "read"])
    assert result.exit_code != 0
    assert "denied" in result.output.lower()
