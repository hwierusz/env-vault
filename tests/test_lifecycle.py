"""Tests for env_vault.lifecycle."""

import pytest
from env_vault.lifecycle import (
    LifecycleError,
    LifecycleEntry,
    set_lifecycle,
    get_lifecycle,
    list_lifecycle,
    remove_lifecycle,
)


def _base_data():
    return {"vars": {"API_KEY": "secret", "DB_URL": "postgres://localhost/db"}}


def _make_load(data):
    def _load(name):
        return data
    return _load


def _make_save(store):
    def _save(name, d):
        store.update(d)
    return _save


def test_set_lifecycle_stores_entry():
    data = _base_data()
    store = dict(data)
    set_lifecycle("v", "API_KEY", "deprecated", None, _make_load(data), _make_save(store))
    assert "__lifecycle__" in data
    assert data["__lifecycle__"]["API_KEY"]["state"] == "deprecated"


def test_set_lifecycle_invalid_state_raises():
    data = _base_data()
    with pytest.raises(LifecycleError, match="Invalid state"):
        set_lifecycle("v", "API_KEY", "unknown", None, _make_load(data), _make_save({}))


def test_set_lifecycle_missing_key_raises():
    data = _base_data()
    with pytest.raises(LifecycleError, match="not found"):
        set_lifecycle("v", "MISSING", "active", None, _make_load(data), _make_save({}))


def test_set_lifecycle_with_note():
    data = _base_data()
    entry = set_lifecycle("v", "API_KEY", "archived", "no longer used", _make_load(data), _make_save({}))
    assert entry.note == "no longer used"


def test_set_lifecycle_preserves_created_at():
    data = _base_data()
    e1 = set_lifecycle("v", "API_KEY", "active", None, _make_load(data), _make_save({}))
    created = e1.created_at
    e2 = set_lifecycle("v", "API_KEY", "deprecated", None, _make_load(data), _make_save({}))
    assert e2.created_at == created


def test_get_lifecycle_returns_entry():
    data = _base_data()
    set_lifecycle("v", "DB_URL", "active", "init", _make_load(data), _make_save({}))
    entry = get_lifecycle("v", "DB_URL", _make_load(data))
    assert isinstance(entry, LifecycleEntry)
    assert entry.state == "active"
    assert entry.note == "init"


def test_get_lifecycle_missing_key_returns_none():
    data = _base_data()
    result = get_lifecycle("v", "NOPE", _make_load(data))
    assert result is None


def test_list_lifecycle_returns_all_entries():
    data = _base_data()
    set_lifecycle("v", "API_KEY", "active", None, _make_load(data), _make_save({}))
    set_lifecycle("v", "DB_URL", "deprecated", None, _make_load(data), _make_save({}))
    entries = list_lifecycle("v", _make_load(data))
    keys = {e.key for e in entries}
    assert keys == {"API_KEY", "DB_URL"}


def test_list_lifecycle_empty_returns_empty_list():
    data = _base_data()
    assert list_lifecycle("v", _make_load(data)) == []


def test_remove_lifecycle_deletes_entry():
    data = _base_data()
    set_lifecycle("v", "API_KEY", "active", None, _make_load(data), _make_save({}))
    removed = remove_lifecycle("v", "API_KEY", _make_load(data), _make_save({}))
    assert removed is True
    assert "API_KEY" not in data["__lifecycle__"]


def test_remove_lifecycle_missing_returns_false():
    data = _base_data()
    result = remove_lifecycle("v", "GHOST", _make_load(data), _make_save({}))
    assert result is False
