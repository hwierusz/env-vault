"""Tests for env_vault.priority."""
import pytest

from env_vault.priority import (
    PriorityError,
    get_priority,
    list_priorities,
    remove_priority,
    set_priority,
    sorted_keys,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_load(data: dict):
    def _load(_vault_name):
        return data
    return _load


def _make_save(store: dict):
    def _save(_vault_name, d):
        store.clear()
        store.update(d)
    return _save


BASE = {"API_KEY": "abc", "DB_URL": "postgres://", "SECRET": "s3cr3t"}


# ---------------------------------------------------------------------------
# set_priority
# ---------------------------------------------------------------------------

def test_set_priority_stores_level():
    data = dict(BASE)
    save_store = {}
    set_priority("v", "API_KEY", 10, _make_load(data), _make_save(save_store))
    assert save_store["__priorities__"]["API_KEY"] == 10


def test_set_priority_missing_key_raises():
    data = dict(BASE)
    with pytest.raises(PriorityError, match="not found"):
        set_priority("v", "MISSING", 5, _make_load(data), _make_save({}))


def test_set_priority_negative_raises():
    data = dict(BASE)
    with pytest.raises(PriorityError, match=">= 0"):
        set_priority("v", "API_KEY", -1, _make_load(data), _make_save({}))


def test_set_priority_zero_is_valid():
    data = dict(BASE)
    save_store = {}
    set_priority("v", "DB_URL", 0, _make_load(data), _make_save(save_store))
    assert save_store["__priorities__"]["DB_URL"] == 0


# ---------------------------------------------------------------------------
# get_priority
# ---------------------------------------------------------------------------

def test_get_priority_returns_stored_level():
    data = {**BASE, "__priorities__": {"SECRET": 99}}
    assert get_priority("v", "SECRET", _make_load(data)) == 99


def test_get_priority_returns_default_when_unset():
    data = dict(BASE)
    assert get_priority("v", "API_KEY", _make_load(data), default=5) == 5


# ---------------------------------------------------------------------------
# remove_priority
# ---------------------------------------------------------------------------

def test_remove_priority_deletes_entry():
    data = {**BASE, "__priorities__": {"API_KEY": 10}}
    save_store = {}
    remove_priority("v", "API_KEY", _make_load(data), _make_save(save_store))
    assert "API_KEY" not in save_store.get("__priorities__", {})


def test_remove_priority_missing_raises():
    data = dict(BASE)
    with pytest.raises(PriorityError, match="No priority set"):
        remove_priority("v", "API_KEY", _make_load(data), _make_save({}))


# ---------------------------------------------------------------------------
# list_priorities
# ---------------------------------------------------------------------------

def test_list_priorities_sorted_descending():
    data = {**BASE, "__priorities__": {"API_KEY": 5, "SECRET": 20, "DB_URL": 1}}
    result = list_priorities("v", _make_load(data))
    levels = [lvl for _, lvl in result]
    assert levels == sorted(levels, reverse=True)


def test_list_priorities_empty_when_none_set():
    data = dict(BASE)
    assert list_priorities("v", _make_load(data)) == []


# ---------------------------------------------------------------------------
# sorted_keys
# ---------------------------------------------------------------------------

def test_sorted_keys_highest_priority_first():
    data = {**BASE, "__priorities__": {"DB_URL": 50, "SECRET": 10}}
    keys = sorted_keys("v", _make_load(data))
    assert keys[0] == "DB_URL"
    assert keys[1] == "SECRET"


def test_sorted_keys_excludes_internal_sections():
    data = {**BASE, "__priorities__": {"API_KEY": 1}}
    keys = sorted_keys("v", _make_load(data))
    assert "__priorities__" not in keys
