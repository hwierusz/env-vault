"""Tests for env_vault/cli_pipeline.py"""

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from env_vault.cli_pipeline import pipeline_cmd


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def patched():
    with patch("env_vault.cli_pipeline.vault_exists") as mock_exists, \
         patch("env_vault.cli_pipeline.load_vault") as mock_load, \
         patch("env_vault.cli_pipeline.save_vault") as mock_save:
        mock_exists.return_value = True
        mock_load.return_value = {"db_host": "localhost", "api key": "secret"}
        yield mock_exists, mock_load, mock_save


def test_pipeline_run_missing_vault(runner):
    with patch("env_vault.cli_pipeline.vault_exists", return_value=False):
        result = runner.invoke(pipeline_cmd, ["run", "ghost", "--password", "pw", "--sanitize"])
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_pipeline_run_no_steps_selected(runner, patched):
    result = runner.invoke(pipeline_cmd, ["run", "myvault", "--password", "pw"])
    assert result.exit_code != 0
    assert "No transformation steps" in result.output


def test_pipeline_run_sanitize_step(runner, patched):
    _, mock_load, _ = patched
    mock_load.return_value = {"my-key": "val"}
    result = runner.invoke(pipeline_cmd, ["run", "myvault", "--password", "pw", "--sanitize"])
    assert "sanitize" in result.output
    assert "Pipeline run" in result.output


def test_pipeline_run_redact_step(runner, patched):
    result = runner.invoke(
        pipeline_cmd, ["run", "myvault", "--password", "pw", "--redact"]
    )
    assert result.exit_code == 0
    assert "redact" in result.output


def test_pipeline_run_with_save(runner, patched):
    _, _, mock_save = patched
    result = runner.invoke(
        pipeline_cmd, ["run", "myvault", "--password", "pw", "--sanitize", "--save"]
    )
    assert result.exit_code == 0
    assert "saved" in result.output
    mock_save.assert_called_once()


def test_pipeline_run_dry_run_does_not_save(runner, patched):
    _, _, mock_save = patched
    result = runner.invoke(
        pipeline_cmd, ["run", "myvault", "--password", "pw", "--sanitize"]
    )
    assert result.exit_code == 0
    assert "Dry-run" in result.output
    mock_save.assert_not_called()


def test_pipeline_run_load_error(runner):
    with patch("env_vault.cli_pipeline.vault_exists", return_value=True), \
         patch("env_vault.cli_pipeline.load_vault", side_effect=Exception("bad decrypt")):
        result = runner.invoke(
            pipeline_cmd, ["run", "myvault", "--password", "pw", "--sanitize"]
        )
    assert result.exit_code != 0
    assert "Error loading vault" in result.output
