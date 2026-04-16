"""Tests for env_vault.cli_traceback."""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from env_vault.cli_traceback import traceback_cmd
from env_vault.traceback import TraceEntry


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def patched(tmp_path):
    vault_dir = str(tmp_path)
    with patch("env_vault.cli_traceback.vault_exists") as mock_exists, \
         patch("env_vault.cli_traceback.record_trace") as mock_record, \
         patch("env_vault.cli_traceback.read_traces") as mock_read, \
         patch("env_vault.cli_traceback.clear_traces") as mock_clear:
        mock_exists.return_value = True
        yield {
            "vault_dir": vault_dir,
            "exists": mock_exists,
            "record": mock_record,
            "read": mock_read,
            "clear": mock_clear,
        }


def test_trace_record_success(runner, patched):
    fake = TraceEntry(key="DB", value="x", source="cli")
    patched["record"].return_value = fake
    result = runner.invoke(traceback_cmd, ["record", "myapp", "DB", "x", "--source", "cli"])
    assert result.exit_code == 0
    assert "Recorded trace" in result.output


def test_trace_record_missing_vault(runner, patched):
    patched["exists"].return_value = False
    result = runner.invoke(traceback_cmd, ["record", "ghost", "K", "v", "--source", "cli"])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_trace_show_text(runner, patched):
    entry = TraceEntry(key="DB", value="x", source="import", timestamp="2024-01-01T00:00:00+00:00")
    patched["read"].return_value = [entry]
    result = runner.invoke(traceback_cmd, ["show", "myapp"])
    assert result.exit_code == 0
    assert "DB" in result.output
    assert "import" in result.output


def test_trace_show_json(runner, patched):
    entry = TraceEntry(key="DB", value="x", source="import")
    patched["read"].return_value = [entry]
    result = runner.invoke(traceback_cmd, ["show", "myapp", "--format", "json"])
    assert result.exit_code == 0
    assert "\"key\"" in result.output


def test_trace_show_empty(runner, patched):
    patched["read"].return_value = []
    result = runner.invoke(traceback_cmd, ["show", "myapp"])
    assert result.exit_code == 0
    assert "No trace" in result.output


def test_trace_clear_success(runner, patched):
    patched["clear"].return_value = 3
    result = runner.invoke(traceback_cmd, ["clear", "myapp"])
    assert result.exit_code == 0
    assert "3" in result.output


def test_trace_clear_missing_vault(runner, patched):
    patched["exists"].return_value = False
    result = runner.invoke(traceback_cmd, ["clear", "ghost"])
    assert result.exit_code != 0
