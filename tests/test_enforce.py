"""Tests for env_vault.enforce."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from env_vault.enforce import (
    EnforceError,
    PolicyViolation,
    available_policies,
    enforce_policy,
)
from env_vault.cli_enforce import enforce_cmd


# ---------------------------------------------------------------------------
# available_policies
# ---------------------------------------------------------------------------

def test_available_policies_returns_list():
    result = available_policies()
    assert isinstance(result, list)
    assert len(result) > 0


def test_available_policies_includes_builtins():
    names = available_policies()
    assert "no_empty_values" in names
    assert "uppercase_keys" in names
    assert "no_spaces_in_keys" in names


def test_available_policies_is_sorted():
    names = available_policies()
    assert names == sorted(names)


# ---------------------------------------------------------------------------
# enforce_policy
# ---------------------------------------------------------------------------

def test_no_violations_for_clean_vars():
    vars_ = {"DB_HOST": "localhost", "API_KEY": "secret123"}
    violations = enforce_policy(vars_, ["no_empty_values", "uppercase_keys", "no_spaces_in_keys"])
    assert violations == []


def test_empty_value_flagged():
    vars_ = {"DB_HOST": "   "}
    violations = enforce_policy(vars_, ["no_empty_values"])
    assert len(violations) == 1
    assert violations[0].key == "DB_HOST"
    assert violations[0].policy == "no_empty_values"


def test_lowercase_key_flagged():
    vars_ = {"db_host": "localhost"}
    violations = enforce_policy(vars_, ["uppercase_keys"])
    assert len(violations) == 1
    assert violations[0].key == "db_host"
    assert violations[0].policy == "uppercase_keys"


def test_key_with_space_flagged():
    vars_ = {"DB HOST": "localhost"}
    violations = enforce_policy(vars_, ["no_spaces_in_keys"])
    assert len(violations) == 1
    assert violations[0].policy == "no_spaces_in_keys"


def test_multiple_violations_returned():
    vars_ = {"db host": "", "GOOD_KEY": "value"}
    violations = enforce_policy(vars_, ["no_empty_values", "uppercase_keys", "no_spaces_in_keys"])
    keys = [v.key for v in violations]
    assert keys.count("db host") >= 2  # uppercase + spaces
    assert "GOOD_KEY" not in keys


def test_unknown_policy_raises():
    with pytest.raises(EnforceError, match="Unknown policies"):
        enforce_policy({"KEY": "val"}, ["nonexistent_policy"])


def test_empty_vars_returns_no_violations():
    violations = enforce_policy({}, ["no_empty_values", "uppercase_keys"])
    assert violations == []


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_policies_lists_names(runner):
    result = runner.invoke(enforce_cmd, ["policies"])
    assert result.exit_code == 0
    assert "no_empty_values" in result.output


def test_cli_run_missing_vault(runner):
    result = runner.invoke(enforce_cmd, ["run", "no_such_vault", "pass"])
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_cli_run_json_output_clean(runner, tmp_path, monkeypatch):
    import env_vault.cli_enforce as ce

    monkeypatch.setattr(ce, "vault_exists", lambda _: True)
    monkeypatch.setattr(ce, "load_vault", lambda n, p: {"DB_HOST": "localhost"})

    result = runner.invoke(
        enforce_cmd,
        ["run", "myvault", "pass", "--policy", "uppercase_keys", "--json"],
    )
    assert result.exit_code == 0
    import json
    data = json.loads(result.output)
    assert data == []
