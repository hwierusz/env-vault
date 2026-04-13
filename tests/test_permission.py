"""Tests for env_vault.permission."""

from __future__ import annotations

import copy
import pytest

from env_vault.permission import (
    PermissionError,
    check_permission,
    grant_permission,
    list_permissions,
    revoke_permission,
)


def _base_data():
    return {"SOME_KEY": "value"}


def _make_load(data: dict):
    def _load(vault_name):
        return copy.deepcopy(data)
    return _load


def _make_save(store: dict):
    def _save(vault_name, d):
        store.clear()
        store.update(d)
    return _save


def test_grant_permission_stores_entry():
    store = _base_data()
    load = _make_load(store)
    save = _make_save(store)
    grant_permission("myvault", "alice", "read", load, save)
    assert "read" in store["__permissions__"]["alice"]


def test_grant_multiple_permissions():
    store = _base_data()
    load = _make_load(store)
    save = _make_save(store)
    grant_permission("myvault", "alice", "read", load, save)
    load = _make_load(store)
    grant_permission("myvault", "alice", "write", load, save)
    assert set(store["__permissions__"]["alice"]) == {"read", "write"}


def test_grant_duplicate_is_idempotent():
    store = _base_data()
    load = _make_load(store)
    save = _make_save(store)
    grant_permission("myvault", "alice", "read", load, save)
    load = _make_load(store)
    grant_permission("myvault", "alice", "read", load, save)
    assert store["__permissions__"]["alice"].count("read") == 1


def test_grant_invalid_permission_raises():
    store = _base_data()
    with pytest.raises(PermissionError, match="Invalid permission"):
        grant_permission("myvault", "alice", "superuser", _make_load(store), _make_save(store))


def test_grant_empty_user_raises():
    store = _base_data()
    with pytest.raises(PermissionError, match="non-empty"):
        grant_permission("myvault", "", "read", _make_load(store), _make_save(store))


def test_revoke_permission_removes_entry():
    store = _base_data()
    load = _make_load(store)
    save = _make_save(store)
    grant_permission("myvault", "bob", "write", load, save)
    load = _make_load(store)
    revoke_permission("myvault", "bob", "write", load, save)
    assert "bob" not in store.get("__permissions__", {})


def test_revoke_nonexistent_permission_raises():
    store = _base_data()
    with pytest.raises(PermissionError, match="does not have"):
        revoke_permission("myvault", "charlie", "admin", _make_load(store), _make_save(store))


def test_list_permissions_all_users():
    store = _base_data()
    load = _make_load(store)
    save = _make_save(store)
    grant_permission("myvault", "alice", "read", load, save)
    load = _make_load(store)
    grant_permission("myvault", "bob", "admin", load, save)
    load = _make_load(store)
    result = list_permissions("myvault", None, load)
    assert "alice" in result
    assert "bob" in result


def test_list_permissions_specific_user():
    store = _base_data()
    load = _make_load(store)
    save = _make_save(store)
    grant_permission("myvault", "alice", "read", load, save)
    load = _make_load(store)
    result = list_permissions("myvault", "alice", load)
    assert result == {"alice": ["read"]}


def test_check_permission_true():
    store = _base_data()
    load = _make_load(store)
    save = _make_save(store)
    grant_permission("myvault", "alice", "write", load, save)
    load = _make_load(store)
    assert check_permission("myvault", "alice", "write", load) is True


def test_check_permission_false():
    store = _base_data()
    assert check_permission("myvault", "nobody", "read", _make_load(store)) is False
