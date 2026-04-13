"""Tests for env_vault.cli_chain."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from env_vault.cli_chain import chain_cmd


@pytest.fixture()
def runner():
    return CliRunner()


# Shared patch targets
_RESOLVE = "env_vault.cli_chain.resolve_chain"
_SOURCES = "env_vault.cli_chain.chain_sources"
_EXISTS = "env_vault.cli_chain.vault_exists"
_LOAD = "env_vault.cli_chain.load_vault"


def test_chain_resolve_success(runner):
    from env_vault.chain import ChainResult

    fake_result = ChainResult(key="DB_URL", value="postgres://localhost", source="prod")
    with patch(_RESOLVE, return_value=fake_result), \
         patch(_EXISTS, return_value=True), \
         patch(_LOAD, return_value={"DB_URL": "postgres://localhost"}):
        result = runner.invoke(
            chain_cmd, ["resolve", "DB_URL", "prod", "dev", "--password", "pw"]
        )
    assert result.exit_code == 0
    assert "postgres://localhost" in result.output
    assert "prod" in result.output


def test_chain_resolve_missing_key(runner):
    from env_vault.chain import ChainError

    with patch(_RESOLVE, side_effect=ChainError("key 'X' not found in any of the vaults")):
        result = runner.invoke(
            chain_cmd, ["resolve", "X", "a", "b", "--password", "pw"]
        )
    assert result.exit_code != 0
    assert "not found" in result.output


def test_chain_show_success(runner):
    merged = {"KEY1": "val1", "KEY2": "val2"}
    with patch(_SOURCES, return_value=merged), \
         patch(_EXISTS, return_value=True), \
         patch(_LOAD, return_value=merged):
        result = runner.invoke(
            chain_cmd, ["show", "a", "b", "--password", "pw"]
        )
    assert result.exit_code == 0
    assert "KEY1=val1" in result.output
    assert "KEY2=val2" in result.output


def test_chain_show_empty_result(runner):
    with patch(_SOURCES, return_value={}), \
         patch(_EXISTS, return_value=True), \
         patch(_LOAD, return_value={}):
        result = runner.invoke(
            chain_cmd, ["show", "empty", "--password", "pw"]
        )
    assert result.exit_code == 0
    assert "no variables" in result.output


def test_chain_show_error(runner):
    from env_vault.chain import ChainError

    with patch(_SOURCES, side_effect=ChainError("vault not found: 'ghost'")):
        result = runner.invoke(
            chain_cmd, ["show", "ghost", "--password", "pw"]
        )
    assert result.exit_code != 0
    assert "ghost" in result.output
