"""Tests for env_vault.cli_classify."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from env_vault.cli_classify import classify_cmd


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


_SAMPLE_VARS = {
    "DB_PASSWORD": "secret",
    "DATABASE_URL": "postgres://localhost/db",
    "APP_PORT": "5432",
    "APP_NAME": "myapp",
}


@pytest.fixture()
def patched():
    with patch("env_vault.cli_classify.load_vault", return_value=_SAMPLE_VARS) as mock:
        yield mock


def test_classify_run_text_output(runner, patched):
    result = runner.invoke(classify_cmd, ["run", "myvault", "pass"])
    assert result.exit_code == 0
    assert "DB_PASSWORD" in result.output
    assert "secret" in result.output
    assert "DATABASE_URL" in result.output


def test_classify_run_json_output(runner, patched):
    result = runner.invoke(classify_cmd, ["run", "myvault", "pass", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    keys = {item["key"] for item in data}
    assert "DB_PASSWORD" in keys
    assert all("category" in item and "confidence" in item for item in data)


def test_classify_run_filter_by_category(runner, patched):
    result = runner.invoke(classify_cmd, ["run", "myvault", "pass", "--category", "secret"])
    assert result.exit_code == 0
    assert "DB_PASSWORD" in result.output
    assert "DATABASE_URL" not in result.output


def test_classify_run_filter_no_match(runner, patched):
    result = runner.invoke(classify_cmd, ["run", "myvault", "pass", "--category", "nonexistent"])
    assert result.exit_code == 0
    assert "No variables match" in result.output


def test_classify_run_load_error(runner):
    with patch("env_vault.cli_classify.load_vault", side_effect=FileNotFoundError("not found")):
        result = runner.invoke(classify_cmd, ["run", "missing", "pass"])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_classify_summary_output(runner, patched):
    result = runner.invoke(classify_cmd, ["summary", "myvault", "pass"])
    assert result.exit_code == 0
    assert "secret" in result.output
    assert "url" in result.output
    assert "config" in result.output


def test_classify_summary_empty_vault(runner):
    with patch("env_vault.cli_classify.load_vault", return_value={}):
        result = runner.invoke(classify_cmd, ["summary", "myvault", "pass"])
    assert result.exit_code == 0
    assert "empty" in result.output.lower()
