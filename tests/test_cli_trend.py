"""Tests for env_vault.cli_trend."""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from env_vault.cli_trend import trend_cmd
from env_vault.trend import TrendEntry


@pytest.fixture()
def runner():
    return CliRunner()


_ENTRIES = [
    TrendEntry(key="DB_URL", total_reads=5, total_writes=2, total_deletes=0,
               last_action="get", last_timestamp="2024-03-01T10:00:00"),
    TrendEntry(key="API_KEY", total_reads=1, total_writes=1, total_deletes=1,
               last_action="delete-03-02T08:00:00"),
]


@pytest.fixture()
def patched():
    with (
        patch("env_vault.cli_trend.vault_exists", return_value=True),
        patch("env_vault.cli_trend.trend_vault", return_value=_ENTRIES),
    ):
        yield


def test_trend_show_text_output(runner, patched):
    result = runner.invoke(trend_cmd, ["show", "myvault"])
    assert result.exit_code == 0
    assert "DB_URL" in result.output
    assert "API_KEY" in result.output


def test_trend_show_json_output(runner, patched):
    result = runner.invoke(trend_cmd, ["show", "myvault", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert data[0]["key"] == "DB_URL"
    assert "activity_score" in data[0]


def test_trend_show_missing_vault(runner):
    with patch("env_vault.cli_trend.vault_exists", return_value=False):
        result = runner.invoke(trend_cmd, ["show", "ghost"])
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_trend_show_top_option(runner):
    many = [
        TrendEntry(key=f"KEY_{i}", total_reads=i, total_writes=0, total_deletes=0)
        for i in range(20)
    ]
    with (
        patch("env_vault.cli_trend.vault_exists", return_value=True),
        patch("env_vault.cli_trend.trend_vault", return_value=many),
    ):
        result = runner.invoke(trend_cmd, ["show", "v", "--top", "3", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 3


def test_trend_show_empty_events(runner):
    with (
        patch("env_vault.cli_trend.vault_exists", return_value=True),
        patch("env_vault.cli_trend.trend_vault", return_value=[]),
    ):
        result = runner.invoke(trend_cmd, ["show", "v"])
    assert result.exit_code == 0
    assert "No audit events" in result.output
