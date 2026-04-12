"""Tests for env_vault.retention."""

from __future__ import annotations

from datetime import datetime, timedelta
from copy import deepcopy

import pytest

from env_vault.retention import (
    RetentionError,
    set_retention,
    get_retention,
    remove_retention,
    list_retention,
)


def _base_data():
    return {"vars": {"API_KEY": "secret", "DB_URL": "postgres://localhost/db"}}


def _make_load(data):
    def _load(vault_name):
        return deepcopy(data)
    return _load


def _make_save(store):
    def _save(vault_name, d):
        store.clear()
        store.update(d)
    return _save


def test_set_retention_stores_entry():
    store = _base_data()
    expiry = set_retention("myvault", "API_KEY", 30, "days", _make_load(store), _make_save(store))
    assert isinstance(expiry, datetime)
    assert "__retention__" in store
    assert "API_KEY" in store["__retention__"]


def test_set_retention_expiry_approximately_correct():
    store = _base_data()
    before = datetime.utcnow() + timedelta(days=29)
    expiry = set_retention("myvault", "API_KEY", 30, "days", _make_load(store), _make_save(store))
    after = datetime.utcnow() + timedelta(days=31)
    assert before < expiry < after


def test_set_retention_weeks_unit():
    store = _base_data()
    expiry = set_retention("myvault", "DB_URL", 2, "weeks", _make_load(store), _make_save(store))
    expected = datetime.utcnow() + timedelta(weeks=2)
    assert abs((expiry - expected).total_seconds()) < 5


def test_set_retention_months_unit():
    store = _base_data()
    expiry = set_retention("myvault", "API_KEY", 1, "months", _make_load(store), _make_save(store))
    expected = datetime.utcnow() + timedelta(days=30)
    assert abs((expiry - expected).total_seconds()) < 5


def test_set_retention_invalid_unit_raises():
    store = _base_data()
    with pytest.raises(RetentionError, match="Invalid unit"):
        set_retention("myvault", "API_KEY", 10, "hours", _make_load(store), _make_save(store))


def test_set_retention_zero_duration_raises():
    store = _base_data()
    with pytest.raises(RetentionError, match="positive"):
        set_retention("myvault", "API_KEY", 0, "days", _make_load(store), _make_save(store))


def test_set_retention_negative_duration_raises():
    store = _base_data()
    with pytest.raises(RetentionError, match="positive"):
        set_retention("myvault", "API_KEY", -5, "days", _make_load(store), _make_save(store))


def test_set_retention_missing_key_raises():
    store = _base_data()
    with pytest.raises(RetentionError, match="not found"):
        set_retention("myvault", "MISSING", 7, "days", _make_load(store), _make_save(store))


def test_get_retention_returns_entry():
    store = _base_data()
    set_retention("myvault", "API_KEY", 10, "days", _make_load(store), _make_save(store))
    entry = get_retention("myvault", "API_KEY", _make_load(store))
    assert entry is not None
    assert entry["duration"] == 10
    assert entry["unit"] == "days"
    assert "expires_at" in entry


def test_get_retention_missing_key_returns_none():
    store = _base_data()
    result = get_retention("myvault", "NOPE", _make_load(store))
    assert result is None


def test_remove_retention_returns_true_when_existed():
    store = _base_data()
    set_retention("myvault", "API_KEY", 5, "days", _make_load(store), _make_save(store))
    removed = remove_retention("myvault", "API_KEY", _make_load(store), _make_save(store))
    assert removed is True


def test_remove_retention_returns_false_when_missing():
    store = _base_data()
    removed = remove_retention("myvault", "API_KEY", _make_load(store), _make_save(store))
    assert removed is False


def test_list_retention_returns_all_entries():
    store = _base_data()
    set_retention("myvault", "API_KEY", 10, "days", _make_load(store), _make_save(store))
    set_retention("myvault", "DB_URL", 2, "weeks", _make_load(store), _make_save(store))
    entries = list_retention("myvault", _make_load(store))
    keys = {e["key"] for e in entries}
    assert keys == {"API_KEY", "DB_URL"}


def test_list_retention_includes_expired_flag():
    store = _base_data()
    set_retention("myvault", "API_KEY", 30, "days", _make_load(store), _make_save(store))
    entries = list_retention("myvault", _make_load(store))
    assert entries[0]["expired"] is False
