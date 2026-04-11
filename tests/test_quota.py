"""Tests for env_vault.quota."""

from __future__ import annotations

import pytest

from env_vault.quota import (
    DEFAULT_QUOTA,
    QuotaError,
    check_quota,
    enforce_quota,
    get_quota,
    remove_quota,
    set_quota,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_load(data: dict):
    def _load(vault_name: str) -> dict:
        return dict(data)
    return _load


def _make_save(store: dict):
    def _save(vault_name: str, payload: dict) -> None:
        store.clear()
        store.update(payload)
    return _save


# ---------------------------------------------------------------------------
# set_quota / get_quota
# ---------------------------------------------------------------------------

def test_set_quota_stores_limit():
    store = {}
    load = _make_load(store)
    save = _make_save(store)
    set_quota("myapp", 50, load, save)
    assert store["__quota__"]["limit"] == 50


def test_get_quota_returns_stored_limit():
    store = {"__quota__": {"limit": 30}}
    load = _make_load(store)
    assert get_quota("myapp", load) == 30


def test_get_quota_returns_default_when_unset():
    store = {}
    load = _make_load(store)
    assert get_quota("myapp", load) == DEFAULT_QUOTA


def test_set_quota_raises_for_zero():
    store = {}
    load = _make_load(store)
    save = _make_save(store)
    with pytest.raises(QuotaError):
        set_quota("myapp", 0, load, save)


def test_set_quota_raises_for_negative():
    store = {}
    load = _make_load(store)
    save = _make_save(store)
    with pytest.raises(QuotaError):
        set_quota("myapp", -5, load, save)


# ---------------------------------------------------------------------------
# remove_quota
# ---------------------------------------------------------------------------

def test_remove_quota_clears_limit():
    store = {"__quota__": {"limit": 20}}
    load = _make_load(store)
    save = _make_save(store)
    remove_quota("myapp", load, save)
    assert "limit" not in store.get("__quota__", {})


# ---------------------------------------------------------------------------
# check_quota
# ---------------------------------------------------------------------------

def test_check_quota_counts_non_meta_keys():
    store = {"FOO": "bar", "BAZ": "qux", "__quota__": {"limit": 10}}
    load = _make_load(store)
    current, limit = check_quota("myapp", load)
    assert current == 2
    assert limit == 10


def test_check_quota_excludes_dunder_keys():
    store = {"__quota__": {"limit": 5}, "__ttl__": {}}
    load = _make_load(store)
    current, limit = check_quota("myapp", load)
    assert current == 0


# ---------------------------------------------------------------------------
# enforce_quota
# ---------------------------------------------------------------------------

def test_enforce_quota_raises_when_at_limit():
    store = {"A": "1", "__quota__": {"limit": 1}}
    load = _make_load(store)
    with pytest.raises(QuotaError, match="reached its quota"):
        enforce_quota("myapp", load)


def test_enforce_quota_passes_when_under_limit():
    store = {"A": "1", "__quota__": {"limit": 10}}
    load = _make_load(store)
    enforce_quota("myapp", load)  # should not raise
