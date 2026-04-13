"""Tests for env_vault.cli_workflow."""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from env_vault.cli_workflow import workflow_cmd
from env_vault.workflow import WorkflowResult


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def patched():
    """Patch storage and workflow functions used by the CLI."""
    with (
        patch("env_vault.cli_workflow.vault_exists") as mock_exists,
        patch("env_vault.cli_workflow.load_vault") as mock_load,
        patch("env_vault.cli_workflow.save_vault") as mock_save,
        patch("env_vault.cli_workflow.run_workflow") as mock_run,
    ):
        mock_exists.return_value = True
        mock_load.return_value = {"KEY": "value"}
        mock_run.return_value = WorkflowResult(
            steps_run=["strip_empty"],
            vars_before={"KEY": "value"},
            vars_after={"KEY": "value"},
        )
        yield {
            "exists": mock_exists,
            "load": mock_load,
            "save": mock_save,
            "run": mock_run,
        }


def test_workflow_run_success(runner, patched):
    result = runner.invoke(
        workflow_cmd, ["run", "myvault", "strip_empty", "--password", "secret"]
    )
    assert result.exit_code == 0
    assert "strip_empty" in result.output


def test_workflow_run_missing_vault(runner, patched):
    patched["exists"].return_value = False
    result = runner.invoke(
        workflow_cmd, ["run", "missing", "strip_empty", "--password", "secret"]
    )
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_workflow_run_unknown_step(runner, patched):
    result = runner.invoke(
        workflow_cmd, ["run", "myvault", "unknown_step", "--password", "secret"]
    )
    assert result.exit_code != 0
    assert "Unknown workflow step" in result.output


def test_workflow_run_dry_run_does_not_save(runner, patched):
    result = runner.invoke(
        workflow_cmd,
        ["run", "myvault", "strip_empty", "--password", "secret", "--dry-run"],
    )
    assert result.exit_code == 0
    patched["save"].assert_not_called()
    assert "dry-run" in result.output


def test_workflow_run_saves_on_success(runner, patched):
    result = runner.invoke(
        workflow_cmd, ["run", "myvault", "strip_empty", "--password", "secret"]
    )
    assert result.exit_code == 0
    patched["save"].assert_called_once()


def test_workflow_run_error_exits_nonzero(runner, patched):
    patched["run"].return_value = WorkflowResult(
        steps_run=[],
        vars_before={},
        vars_after={},
        errors=["strip_empty: boom"],
    )
    result = runner.invoke(
        workflow_cmd, ["run", "myvault", "strip_empty", "--password", "secret"]
    )
    assert result.exit_code != 0
    assert "error" in result.output


def test_workflow_list_shows_steps(runner):
    result = runner.invoke(workflow_cmd, ["list"])
    assert result.exit_code == 0
    assert "strip_empty" in result.output
    assert "uppercase_keys" in result.output
    assert "strip_whitespace" in result.output
