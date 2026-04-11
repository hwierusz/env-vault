"""Tests for env_vault.access."""
from __future__ import annotations

import pytest

from env_vault.access import (
    AccessError,
    _ACCESS_KEY,
    check_access,
    grant_access,
    list_access,
    revoke_access,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_load(data: dict):
    def _load(vault_name):
        return dict(data)
    return _load


def _make_save(store: dict):
    def _save(vault_name, d):
        store.clear()
        store.update(d)
    return _save


@pytest.fixture()
def empty_vault():
    store = {"DB_URL": "postgres://localhost/dev"}
    saved = dict(store)
    return store, saved


# ---------------------------------------------------------------------------
# grant_access
# ---------------------------------------------------------------------------

def test_grant_stores_permission():
    store = {}
    saved = {}
    grant_access("myapp", "alice", ["read"], _make_load(store), _make_save(saved))
    assert "alice" in saved[_ACCESS_KEY]
    assert "read" in saved[_ACCESS_KEY]["alice"]


def test_grant_multiple_permissions():
    store = {}
    saved = {}
    grant_access("myapp", "bob", ["read", "write"], _make_load(store), _make_save(saved))
    assert set(saved[_ACCESS_KEY]["bob"]) == {"read", "write"}


def test_grant_merges_with_existing():
    store = {_ACCESS_KEY: {"alice": ["read"]}}
    saved = {}
    grant_access("myapp", "alice", ["write"], _make_load(store), _make_save(saved))
    assert set(saved[_ACCESS_KEY]["alice"]) == {"read", "write"}


def test_grant_invalid_permission_raises():
    with pytest.raises(AccessError, match="Unknown permissions"):
        grant_access("myapp", "eve", ["delete"], _make_load({}), _make_save({}))


# ---------------------------------------------------------------------------
# revoke_access
# ---------------------------------------------------------------------------

def test_revoke_specific_permission():
    store = {_ACCESS_KEY: {"alice": ["read", "write"]}}
    saved = {}
    revoke_access("myapp", "alice", ["write"], _make_load(store), _make_save(saved))
    assert saved[_ACCESS_KEY]["alice"] == ["read"]


def test_revoke_all_removes_user():
    store = {_ACCESS_KEY: {"alice": ["read", "write"]}}
    saved = {}
    revoke_access("myapp", "alice", None, _make_load(store), _make_save(saved))
    assert "alice" not in saved[_ACCESS_KEY]


def test_revoke_unknown_user_raises():
    store = {_ACCESS_KEY: {}}
    with pytest.raises(AccessError, match="no access entry"):
        revoke_access("myapp", "ghost", None, _make_load(store), _make_save({}))


# ---------------------------------------------------------------------------
# list_access
# ---------------------------------------------------------------------------

def test_list_access_returns_acl():
    store = {_ACCESS_KEY: {"alice": ["read"], "bob": ["admin"]}}
    acl = list_access("myapp", _make_load(store))
    assert acl == {"alice": ["read"], "bob": ["admin"]}


def test_list_access_empty_when_no_acl():
    acl = list_access("myapp", _make_load({}))
    assert acl == {}


# ---------------------------------------------------------------------------
# check_access
# ---------------------------------------------------------------------------

def test_check_access_open_vault_always_true():
    assert check_access("myapp", "write", _make_load({})) is True


def test_check_access_admin_grants_all(monkeypatch):
    monkeypatch.setattr("env_vault.access.getpass.getuser", lambda: "carol")
    store = {_ACCESS_KEY: {"carol": ["admin"]}}
    assert check_access("myapp", "write", _make_load(store)) is True


def test_check_access_denied_for_missing_user(monkeypatch):
    monkeypatch.setattr("env_vault.access.getpass.getuser", lambda: "stranger")
    store = {_ACCESS_KEY: {"alice": ["read"]}}
    assert check_access("myapp", "read", _make_load(store)) is False
