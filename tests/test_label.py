"""Tests for env_vault.label."""

from __future__ import annotations

from typing import Any, Dict

import pytest

from env_vault.label import LabelError, add_label, find_by_label, list_labels, remove_label


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_load(data: dict):
    def _load(_vault_name: str) -> dict:
        return data
    return _load


def _make_save(store: dict):
    def _save(_vault_name: str, d: dict) -> None:
        store.clear()
        store.update(d)
    return _save


def _base_data() -> dict:
    return {"vars": {"DB_URL": "postgres://localhost", "API_KEY": "secret"}}


# ---------------------------------------------------------------------------
# add_label
# ---------------------------------------------------------------------------

def test_add_label_stores_label():
    data = _base_data()
    store: dict = {}
    store.update(data)
    add_label("v", "DB_URL", "production", _make_load(store), _make_save(store))
    assert "production" in store["__labels__"]["DB_URL"]


def test_add_label_idempotent():
    data = _base_data()
    store: dict = {}
    store.update(data)
    add_label("v", "DB_URL", "production", _make_load(store), _make_save(store))
    add_label("v", "DB_URL", "production", _make_load(store), _make_save(store))
    assert store["__labels__"]["DB_URL"].count("production") == 1


def test_add_label_missing_key_raises():
    data = _base_data()
    with pytest.raises(LabelError, match="MISSING"):
        add_label("v", "MISSING", "x", _make_load(data), _make_save({}))


def test_add_multiple_labels_to_same_key():
    data = _base_data()
    store: dict = {}
    store.update(data)
    add_label("v", "API_KEY", "secret", _make_load(store), _make_save(store))
    add_label("v", "API_KEY", "critical", _make_load(store), _make_save(store))
    assert set(store["__labels__"]["API_KEY"]) == {"secret", "critical"}


# ---------------------------------------------------------------------------
# remove_label
# ---------------------------------------------------------------------------

def test_remove_label_removes_entry():
    data = _base_data()
    data["__labels__"] = {"DB_URL": ["production", "legacy"]}
    store: dict = {}
    store.update(data)
    remove_label("v", "DB_URL", "legacy", _make_load(store), _make_save(store))
    assert "legacy" not in store["__labels__"]["DB_URL"]
    assert "production" in store["__labels__"]["DB_URL"]


def test_remove_label_absent_is_noop():
    data = _base_data()
    data["__labels__"] = {"DB_URL": ["production"]}
    store: dict = {}
    store.update(data)
    remove_label("v", "DB_URL", "nonexistent", _make_load(store), _make_save(store))
    assert store["__labels__"]["DB_URL"] == ["production"]


# ---------------------------------------------------------------------------
# list_labels
# ---------------------------------------------------------------------------

def test_list_labels_returns_all_labels():
    data = _base_data()
    data["__labels__"] = {"DB_URL": ["production", "legacy"], "API_KEY": ["secret"]}
    result = list_labels("v", _make_load(data))
    assert result == {"DB_URL": ["production", "legacy"], "API_KEY": ["secret"]}


def test_list_labels_empty_when_no_labels():
    data = _base_data()
    result = list_labels("v", _make_load(data))
    assert result == {}


# ---------------------------------------------------------------------------
# find_by_label
# ---------------------------------------------------------------------------

def test_find_by_label_returns_matching_keys():
    data = _base_data()
    data["__labels__"] = {"DB_URL": ["production"], "API_KEY": ["production", "secret"]}
    result = find_by_label("v", "production", _make_load(data))
    assert set(result) == {"DB_URL", "API_KEY"}


def test_find_by_label_no_matches_returns_empty():
    data = _base_data()
    data["__labels__"] = {"DB_URL": ["production"]}
    result = find_by_label("v", "staging", _make_load(data))
    assert result == []
