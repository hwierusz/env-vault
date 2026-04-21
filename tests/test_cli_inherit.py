"""Tests for env_vault.cli_inherit."""
from __future__ import annotations

from typing import Dict
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from env_vault.cli_inherit import inherit_cmd
from env_vault.inherit import InheritError, InheritResult


@pytest.fixture()
def runner():
    return CliRunner()


def _result(key="FOO", value="bar", source="child", depth=0):
    return InheritResult(key=key, value=value, source_vault=source, depth=depth)


@pytest.fixture()
def patched():
    with (
        patch("env_vault.cli_inherit.resolve_inherited") as mock_resolve,
        patch("env_vault.cli_inherit.inherit_all") as mock_all,
        patch("env_vault.cli_inherit.vault_exists", return_value=True),
        patch("env_vault.cli_inherit.load_vault", return_value={}),
    ):
        yield mock_resolve, mock_all


def test_inherit_resolve_success(runner, patched):
    mock_resolve, _ = patched
    mock_resolve.return_value = _result()
    result = runner.invoke(
        inherit_cmd,
        ["resolve", "FOO", "--vault", "child", "--vault", "parent",
         "--password", "pw"],
    )
    assert result.exit_code == 0
    assert "FOO=bar" in result.output
    assert "child" in result.output


def test_inherit_resolve_json_output(runner, patched):
    mock_resolve, _ = patched
    mock_resolve.return_value = _result()
    result = runner.invoke(
        inherit_cmd,
        ["resolve", "FOO", "--vault", "child", "--json", "--password", "pw"],
    )
    assert result.exit_code == 0
    import json
    data = json.loads(result.output)
    assert data["key"] == "FOO"
    assert data["value"] == "bar"


def test_inherit_resolve_error(runner, patched):
    mock_resolve, _ = patched
    mock_resolve.side_effect = InheritError("Key not found")
    result = runner.invoke(
        inherit_cmd,
        ["resolve", "MISSING", "--vault", "v", "--password", "pw"],
    )
    assert result.exit_code != 0
    assert "Key not found" in result.output


def test_inherit_show_success(runner, patched):
    _, mock_all = patched
    mock_all.return_value = {
        "A": _result("A", "1", "child", 0),
        "B": _result("B", "2", "parent", 1),
    }
    result = runner.invoke(
        inherit_cmd,
        ["show", "--vault", "child", "--vault", "parent", "--password", "pw"],
    )
    assert result.exit_code == 0
    assert "A=1" in result.output
    assert "B=2" in result.output


def test_inherit_show_json_output(runner, patched):
    _, mock_all = patched
    mock_all.return_value = {"X": _result("X", "42", "base", 0)}
    result = runner.invoke(
        inherit_cmd,
        ["show", "--vault", "base", "--json", "--password", "pw"],
    )
    assert result.exit_code == 0
    import json
    data = json.loads(result.output)
    assert data["X"]["value"] == "42"


def test_inherit_show_error(runner, patched):
    _, mock_all = patched
    mock_all.side_effect = InheritError("Vault not found: ghost")
    result = runner.invoke(
        inherit_cmd,
        ["show", "--vault", "ghost", "--password", "pw"],
    )
    assert result.exit_code != 0
    assert "ghost" in result.output
