"""Tests for env_vault.cli_token CLI commands."""
import json
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from env_vault.cli_token import token_cmd
from env_vault.token import TokenError


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def patched():
    with patch("env_vault.cli_token.vault_exists") as ve, \
         patch("env_vault.cli_token.load_vault") as lv, \
         patch("env_vault.cli_token.save_vault") as sv:
        ve.return_value = True
        lv.return_value = {"DB_URL": "postgres://localhost"}
        yield ve, lv, sv


def test_token_issue_success(runner, patched):
    ve, lv, sv = patched
    with patch("env_vault.cli_token.issue_token", return_value="abc" * 21 + "ab") as it:
        result = runner.invoke(token_cmd, ["issue", "myvault", "ci", "DB_URL", "--password", "pass"])
    assert result.exit_code == 0
    assert "Token issued" in result.output


def test_token_issue_missing_vault(runner, patched):
    ve, lv, sv = patched
    ve.return_value = False
    result = runner.invoke(token_cmd, ["issue", "missing", "ci", "DB_URL", "--password", "pass"])
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_token_issue_token_error(runner, patched):
    with patch("env_vault.cli_token.issue_token", side_effect=TokenError("Key not found")):
        result = runner.invoke(token_cmd, ["issue", "myvault", "ci", "MISSING", "--password", "pass"])
    assert result.exit_code != 0
    assert "Key not found" in result.output


def test_token_revoke_success(runner, patched):
    ve, lv, sv = patched
    with patch("env_vault.cli_token.revoke_token") as rt:
        result = runner.invoke(token_cmd, ["revoke", "myvault", "sometoken", "--password", "pass"])
    assert result.exit_code == 0
    assert "revoked" in result.output


def test_token_resolve_text_output(runner, patched):
    ve, lv, sv = patched
    with patch("env_vault.cli_token.resolve_token", return_value={"DB_URL": "postgres://localhost"}):
        result = runner.invoke(token_cmd, ["resolve", "myvault", "tok", "--password", "pass"])
    assert "DB_URL=postgres://localhost" in result.output


def test_token_resolve_json_output(runner, patched):
    ve, lv, sv = patched
    with patch("env_vault.cli_token.resolve_token", return_value={"DB_URL": "postgres://localhost"}):
        result = runner.invoke(token_cmd, ["resolve", "myvault", "tok", "--password", "pass", "--format", "json"])
    parsed = json.loads(result.output)
    assert parsed["DB_URL"] == "postgres://localhost"


def test_token_list_empty(runner, patched):
    with patch("env_vault.cli_token.list_tokens", return_value=[]):
        result = runner.invoke(token_cmd, ["list", "myvault", "--password", "pass"])
    assert "No tokens" in result.output


def test_token_list_shows_entries(runner, patched):
    entries = [{"token": "abcd1234...", "label": "ci", "allowed_keys": ["DB_URL"], "expired": False}]
    with patch("env_vault.cli_token.list_tokens", return_value=entries):
        result = runner.invoke(token_cmd, ["list", "myvault", "--password", "pass"])
    assert "ci" in result.output
    assert "active" in result.output


def test_token_purge_reports_count(runner, patched):
    ve, lv, sv = patched
    with patch("env_vault.cli_token.purge_expired_tokens", return_value=3):
        result = runner.invoke(token_cmd, ["purge", "myvault", "--password", "pass"])
    assert "3" in result.output
    assert sv.called
