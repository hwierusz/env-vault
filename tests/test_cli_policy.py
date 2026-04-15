"""Tests for env_vault.cli_policy."""
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from env_vault.cli_policy import policy_cmd
from env_vault.policy import PolicyResult


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def patched():
    with patch("env_vault.cli_policy.vault_exists", return_value=True) as ve, \
         patch("env_vault.cli_policy.load_vault", return_value={"DB_HOST": "localhost"}) as lv, \
         patch("env_vault.cli_policy.save_vault") as sv, \
         patch("env_vault.cli_policy.assign_policy") as ap, \
         patch("env_vault.cli_policy.unassign_policy") as up, \
         patch("env_vault.cli_policy.list_policies_for", return_value=["uppercase_keys"]) as lpf, \
         patch("env_vault.cli_policy.evaluate_policies", return_value=[
             PolicyResult(policy="uppercase_keys", passed=True)
         ]) as ep:
        yield {"ve": ve, "lv": lv, "sv": sv, "ap": ap, "up": up, "lpf": lpf, "ep": ep}


def test_policy_assign_success(runner, patched):
    result = runner.invoke(policy_cmd, ["assign", "default", "uppercase_keys"], input="secret\nsecret\n")
    assert result.exit_code == 0
    assert "assigned" in result.output
    patched["ap"].assert_called_once()


def test_policy_assign_missing_vault(runner):
    with patch("env_vault.cli_policy.vault_exists", return_value=False):
        result = runner.invoke(policy_cmd, ["assign", "missing", "uppercase_keys"], input="secret\nsecret\n")
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_policy_assign_unknown_policy(runner, patched):
    from env_vault.policy import PolicyError
    patched["ap"].side_effect = PolicyError("Unknown policy")
    result = runner.invoke(policy_cmd, ["assign", "default", "bad_policy"], input="secret\nsecret\n")
    assert result.exit_code != 0
    assert "Error" in result.output


def test_policy_unassign_success(runner, patched):
    result = runner.invoke(policy_cmd, ["unassign", "default", "uppercase_keys"], input="secret\nsecret\n")
    assert result.exit_code == 0
    assert "removed" in result.output


def test_policy_list_shows_policies(runner, patched):
    result = runner.invoke(policy_cmd, ["list", "default"], input="secret\nsecret\n")
    assert result.exit_code == 0
    assert "uppercase_keys" in result.output


def test_policy_list_empty(runner, patched):
    patched["lpf"].return_value = []
    result = runner.invoke(policy_cmd, ["list", "default"], input="secret\nsecret\n")
    assert result.exit_code == 0
    assert "No policies" in result.output


def test_policy_evaluate_text(runner, patched):
    result = runner.invoke(policy_cmd, ["evaluate", "default"], input="secret\nsecret\n")
    assert result.exit_code == 0
    assert "PASS" in result.output
    assert "uppercase_keys" in result.output


def test_policy_evaluate_json(runner, patched):
    result = runner.invoke(policy_cmd, ["evaluate", "default", "--json"], input="secret\nsecret\n")
    assert result.exit_code == 0
    assert "\"policy\"" in result.output or '"policy"' in result.output
