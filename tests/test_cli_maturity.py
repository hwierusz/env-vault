"""Tests for env_vault.cli_maturity."""
import json
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from env_vault.cli_maturity import maturity_cmd
from env_vault.maturity import MaturityReport, MaturityError


@pytest.fixture
def runner():
    return CliRunner()


import pytest


def _report():
    return MaturityReport(
        vault_name="prod",
        scores={"ttl_coverage": 80, "audit_activity": 60, "key_hygiene": 100},
    )


@pytest.fixture
def patched():
    with patch("env_vault.cli_maturity.assess_maturity", return_value=_report()) as m:
        yield m


def test_maturity_show_text_output(patched):
    r = CliRunner()
    result = r.invoke(maturity_cmd, ["show", "prod", "--password", "pw"])
    assert result.exit_code == 0
    assert "prod" in result.output
    assert "key_hygiene" in result.output


def test_maturity_show_json_output(patched):
    r = CliRunner()
    result = r.invoke(maturity_cmd, ["show", "prod", "--password", "pw", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["vault"] == "prod"
    assert "scores" in data
    assert "level" in data


def test_maturity_show_missing_vault():
    r = CliRunner()
    with patch("env_vault.cli_maturity.assess_maturity", side_effect=MaturityError("not found")):
        result = r.invoke(maturity_cmd, ["show", "missing", "--password", "pw"])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_maturity_levels_lists_all():
    r = CliRunner()
    result = r.invoke(maturity_cmd, ["levels"])
    assert result.exit_code == 0
    assert "optimizing" in result.output
    assert "initial" in result.output
