"""Tests for env_vault.cli_forecast."""
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from env_vault.cli_forecast import forecast_cmd
from env_vault.forecast import ForecastEntry, ForecastError


NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture()
def runner():
    return CliRunner()


def _entry(key, delta_seconds, status="ok"):
    expiry = NOW + timedelta(seconds=delta_seconds)
    return ForecastEntry(
        key=key,
        expires_at=expiry,
        seconds_remaining=float(delta_seconds),
        status=status,
    )


@pytest.fixture()
def patched():
    with patch("env_vault.cli_forecast.forecast_vault") as mock_fn:
        yield mock_fn


def test_forecast_show_text_output(runner, patched):
    patched.return_value = [_entry("DB_PASS", 200000)]
    result = runner.invoke(
        forecast_cmd, ["show", "myvault", "--password", "secret"]
    )
    assert result.exit_code == 0
    assert "DB_PASS" in result.output


def test_forecast_show_json_output(runner, patched):
    patched.return_value = [_entry("API_KEY", 100000)]
    result = runner.invoke(
        forecast_cmd,
        ["show", "myvault", "--password", "secret", "--format", "json"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert isinstance(payload, list)
    assert payload[0]["key"] == "API_KEY"
    assert "expires_at" in payload[0]
    assert "status" in payload[0]


def test_forecast_show_no_entries(runner, patched):
    patched.return_value = []
    result = runner.invoke(
        forecast_cmd, ["show", "myvault", "--password", "secret"]
    )
    assert result.exit_code == 0
    assert "No TTL-enabled" in result.output


def test_forecast_show_filter_expired(runner, patched):
    patched.return_value = [
        _entry("OLD", -100, status="expired"),
        _entry("FRESH", 90000, status="ok"),
    ]
    result = runner.invoke(
        forecast_cmd,
        ["show", "myvault", "--password", "secret", "--filter", "expired"],
    )
    assert result.exit_code == 0
    assert "OLD" in result.output
    assert "FRESH" not in result.output


def test_forecast_show_filter_warning(runner, patched):
    patched.return_value = [
        _entry("WARN_KEY", 3600, status="warning"),
    ]
    result = runner.invoke(
        forecast_cmd,
        ["show", "myvault", "--password", "secret", "--filter", "warning"],
    )
    assert result.exit_code == 0
    assert "WARN_KEY" in result.output


def test_forecast_show_error_propagates(runner, patched):
    patched.side_effect = ForecastError("vault not found")
    result = runner.invoke(
        forecast_cmd, ["show", "myvault", "--password", "secret"]
    )
    assert result.exit_code != 0
    assert "vault not found" in result.output
