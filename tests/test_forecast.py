"""Tests for env_vault.forecast."""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from env_vault.forecast import ForecastEntry, ForecastError, forecast_vault, _classify


NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _make_loader(data: dict):
    def _load(vault_name, password):
        return data
    return _load


def _make_ttl(mapping: dict):
    def _get_ttl(data, key):
        return mapping.get(key)
    return _get_ttl


# --- _classify ---

def test_classify_ok():
    assert _classify(90000, 86400) == "ok"


def test_classify_warning():
    assert _classify(3600, 86400) == "warning"


def test_classify_expired():
    assert _classify(-1, 86400) == "expired"


def test_classify_boundary_warning():
    assert _classify(86400, 86400) == "warning"


# --- forecast_vault ---

def test_forecast_returns_entries_for_keys_with_ttl():
    expiry = NOW + timedelta(hours=48)
    data = {"vars": {"KEY_A": "val", "KEY_B": "val"}}
    entries = forecast_vault(
        "myvault", "pass",
        load_fn=_make_loader(data),
        ttl_fn=_make_ttl({"KEY_A": expiry}),
        now=NOW,
    )
    assert len(entries) == 1
    assert entries[0].key == "KEY_A"


def test_forecast_skips_keys_without_ttl():
    data = {"vars": {"NO_TTL": "x"}}
    entries = forecast_vault(
        "v", "p",
        load_fn=_make_loader(data),
        ttl_fn=_make_ttl({}),
        now=NOW,
    )
    assert entries == []


def test_forecast_status_ok():
    expiry = NOW + timedelta(days=5)
    data = {"vars": {"K": "v"}}
    entries = forecast_vault(
        "v", "p",
        load_fn=_make_loader(data),
        ttl_fn=_make_ttl({"K": expiry}),
        now=NOW,
    )
    assert entries[0].status == "ok"


def test_forecast_status_warning():
    expiry = NOW + timedelta(hours=1)
    data = {"vars": {"K": "v"}}
    entries = forecast_vault(
        "v", "p",
        load_fn=_make_loader(data),
        ttl_fn=_make_ttl({"K": expiry}),
        now=NOW,
        warning_threshold=86400,
    )
    assert entries[0].status == "warning"


def test_forecast_status_expired():
    expiry = NOW - timedelta(seconds=1)
    data = {"vars": {"K": "v"}}
    entries = forecast_vault(
        "v", "p",
        load_fn=_make_loader(data),
        ttl_fn=_make_ttl({"K": expiry}),
        now=NOW,
    )
    assert entries[0].status == "expired"


def test_forecast_sorted_by_expiry():
    soon = NOW + timedelta(hours=1)
    later = NOW + timedelta(days=3)
    data = {"vars": {"LATER": "v", "SOON": "v"}}
    entries = forecast_vault(
        "v", "p",
        load_fn=_make_loader(data),
        ttl_fn=_make_ttl({"LATER": later, "SOON": soon}),
        now=NOW,
    )
    assert entries[0].key == "SOON"
    assert entries[1].key == "LATER"


def test_forecast_raises_on_load_error():
    def bad_load(name, pw):
        raise RuntimeError("disk error")

    with pytest.raises(ForecastError, match="disk error"):
        forecast_vault("v", "p", load_fn=bad_load, ttl_fn=_make_ttl({}))


def test_forecast_entry_seconds_remaining():
    expiry = NOW + timedelta(seconds=300)
    data = {"vars": {"K": "v"}}
    entries = forecast_vault(
        "v", "p",
        load_fn=_make_loader(data),
        ttl_fn=_make_ttl({"K": expiry}),
        now=NOW,
    )
    assert abs(entries[0].seconds_remaining - 300) < 1
