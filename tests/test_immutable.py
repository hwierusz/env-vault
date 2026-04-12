"""Tests for env_vault.immutable."""

import pytest
from env_vault.immutable import (
    lock_key, unlock_key, is_locked, list_locked, assert_mutable, ImmutableError,
)


def _make_load(data: dict):
    def _load(vault_name):
        return data
    return _load


def _make_save(store: list):
    def _save(vault_name, data):
        store.clear()
        store.append(data)
    return _save


@pytest.fixture()
def base_data():
    return {"vars": {"API_KEY": "secret", "DEBUG": "true"}, "__immutable__": {}}


def test_lock_key_stores_entry(base_data):
    saved = []
    lock_key("myvault", "API_KEY", reason="critical",
             load_fn=_make_load(base_data), save_fn=_make_save(saved))
    assert "API_KEY" in saved[0]["__immutable__"]
    assert saved[0]["__immutable__"]["API_KEY"]["reason"] == "critical"


def test_lock_key_missing_key_raises(base_data):
    with pytest.raises(ImmutableError, match="does not exist"):
        lock_key("myvault", "MISSING", load_fn=_make_load(base_data), save_fn=_make_save([]))


def test_unlock_key_removes_entry(base_data):
    base_data["__immutable__"]["API_KEY"] = {"reason": ""}
    saved = []
    unlock_key("myvault", "API_KEY",
               load_fn=_make_load(base_data), save_fn=_make_save(saved))
    assert "API_KEY" not in saved[0]["__immutable__"]


def test_unlock_key_not_locked_raises(base_data):
    with pytest.raises(ImmutableError, match="is not locked"):
        unlock_key("myvault", "DEBUG",
                   load_fn=_make_load(base_data), save_fn=_make_save([]))


def test_is_locked_true(base_data):
    base_data["__immutable__"]["API_KEY"] = {"reason": ""}
    assert is_locked("myvault", "API_KEY", load_fn=_make_load(base_data)) is True


def test_is_locked_false(base_data):
    assert is_locked("myvault", "DEBUG", load_fn=_make_load(base_data)) is False


def test_list_locked_returns_all(base_data):
    base_data["__immutable__"] = {
        "API_KEY": {"reason": "do not touch"},
        "TOKEN": {"reason": ""},
    }
    result = list_locked("myvault", load_fn=_make_load(base_data))
    assert set(result.keys()) == {"API_KEY", "TOKEN"}


def test_list_locked_empty(base_data):
    result = list_locked("myvault", load_fn=_make_load(base_data))
    assert result == {}


def test_assert_mutable_passes_when_unlocked(base_data):
    assert_mutable("myvault", "DEBUG", load_fn=_make_load(base_data))  # no exception


def test_assert_mutable_raises_when_locked(base_data):
    base_data["__immutable__"]["API_KEY"] = {"reason": ""}
    with pytest.raises(ImmutableError, match="immutable"):
        assert_mutable("myvault", "API_KEY", load_fn=_make_load(base_data))
