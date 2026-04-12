"""Tests for env_vault.cli_label."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from env_vault.cli_label import label_cmd


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def patched():
    """Patch storage and label module functions used by the CLI."""
    with (
        patch("env_vault.cli_label.vault_exists", return_value=True) as ve,
        patch("env_vault.cli_label.add_label") as al,
        patch("env_vault.cli_label.remove_label") as rl,
        patch("env_vault.cli_label.list_labels", return_value=["prod", "critical"]) as ll,
        patch("env_vault.cli_label.find_by_label", return_value={"DB_URL": ["prod"]}) as fl,
    ):
        yield {"vault_exists": ve, "add_label": al, "remove_label": rl,
               "list_labels": ll, "find_by_label": fl}


def test_label_add_success(runner, patched):
    result = runner.invoke(label_cmd, ["add", "myvault", "DB_URL", "prod"])
    assert result.exit_code == 0
    assert "added" in result.output
    patched["add_label"].assert_called_once()


def test_label_add_missing_vault(runner, patched):
    patched["vault_exists"].return_value = False
    result = runner.invoke(label_cmd, ["add", "ghost", "DB_URL", "prod"])
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_label_add_label_error(runner, patched):
    from env_vault.label import LabelError
    patched["add_label"].side_effect = LabelError("Key 'X' not found")
    result = runner.invoke(label_cmd, ["add", "myvault", "X", "prod"])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_label_remove_success(runner, patched):
    result = runner.invoke(label_cmd, ["remove", "myvault", "DB_URL", "prod"])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_label_list_shows_labels(runner, patched):
    result = runner.invoke(label_cmd, ["list", "myvault", "DB_URL"])
    assert result.exit_code == 0
    assert "prod" in result.output
    assert "critical" in result.output


def test_label_list_empty(runner, patched):
    patched["list_labels"].return_value = []
    result = runner.invoke(label_cmd, ["list", "myvault", "DB_URL"])
    assert result.exit_code == 0
    assert "No labels" in result.output


def test_label_find_shows_keys(runner, patched):
    result = runner.invoke(label_cmd, ["find", "myvault", "prod"])
    assert result.exit_code == 0
    assert "DB_URL" in result.output


def test_label_find_no_match(runner, patched):
    patched["find_by_label"].return_value = {}
    result = runner.invoke(label_cmd, ["find", "myvault", "unknown"])
    assert result.exit_code == 0
    assert "No keys found" in result.output
