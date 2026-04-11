"""Tests for env_vault.namespace."""

import pytest
from env_vault.namespace import (
    assign_to_namespace,
    remove_from_namespace,
    list_namespaces,
    get_namespace_vars,
    NamespaceError,
    NAMESPACE_KEY,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_load(data: dict):
    def _load(vault_name, password):
        return dict(data)
    return _load


def _make_save(store: dict):
    def _save(vault_name, password, data):
        store.clear()
        store.update(data)
    return _save


BASE = {"DB_URL": "postgres://localhost", "API_KEY": "secret", "PORT": "5432"}


# ---------------------------------------------------------------------------
# assign_to_namespace
# ---------------------------------------------------------------------------

def test_assign_stores_key_in_namespace():
    store = dict(BASE)
    assign_to_namespace("v", "DB_URL", "database", _make_load(store), _make_save(store), "pw")
    assert "DB_URL" in store[NAMESPACE_KEY]["database"]


def test_assign_raises_for_missing_key():
    store = dict(BASE)
    with pytest.raises(NamespaceError, match="not found"):
        assign_to_namespace("v", "MISSING", "ns", _make_load(store), _make_save(store), "pw")


def test_assign_raises_for_invalid_namespace_name():
    store = dict(BASE)
    with pytest.raises(NamespaceError, match="Invalid namespace"):
        assign_to_namespace("v", "DB_URL", "bad name!", _make_load(store), _make_save(store), "pw")


def test_assign_moves_key_between_namespaces():
    store = {**BASE, NAMESPACE_KEY: {"old_ns": ["DB_URL"]}}
    assign_to_namespace("v", "DB_URL", "new_ns", _make_load(store), _make_save(store), "pw")
    assert "DB_URL" not in store[NAMESPACE_KEY].get("old_ns", [])
    assert "DB_URL" in store[NAMESPACE_KEY]["new_ns"]


# ---------------------------------------------------------------------------
# remove_from_namespace
# ---------------------------------------------------------------------------

def test_remove_from_namespace_succeeds():
    store = {**BASE, NAMESPACE_KEY: {"database": ["DB_URL"]}}
    remove_from_namespace("v", "DB_URL", "database", _make_load(store), _make_save(store), "pw")
    assert "database" not in store.get(NAMESPACE_KEY, {})


def test_remove_raises_if_key_not_in_namespace():
    store = {**BASE, NAMESPACE_KEY: {"database": ["PORT"]}}
    with pytest.raises(NamespaceError):
        remove_from_namespace("v", "DB_URL", "database", _make_load(store), _make_save(store), "pw")


# ---------------------------------------------------------------------------
# list_namespaces
# ---------------------------------------------------------------------------

def test_list_namespaces_returns_dict():
    store = {**BASE, NAMESPACE_KEY: {"database": ["DB_URL"], "app": ["PORT"]}}
    result = list_namespaces("v", _make_load(store), "pw")
    assert result == {"database": ["DB_URL"], "app": ["PORT"]}


def test_list_namespaces_empty_when_none():
    result = list_namespaces("v", _make_load(BASE), "pw")
    assert result == {}


# ---------------------------------------------------------------------------
# get_namespace_vars
# ---------------------------------------------------------------------------

def test_get_namespace_vars_returns_correct_pairs():
    store = {**BASE, NAMESPACE_KEY: {"database": ["DB_URL", "PORT"]}}
    result = get_namespace_vars("v", "database", _make_load(store), "pw")
    assert result == {"DB_URL": "postgres://localhost", "PORT": "5432"}


def test_get_namespace_vars_raises_for_unknown_namespace():
    with pytest.raises(NamespaceError, match="does not exist"):
        get_namespace_vars("v", "nonexistent", _make_load(BASE), "pw")
