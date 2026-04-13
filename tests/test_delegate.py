"""Tests for env_vault.delegate."""
import pytest

from env_vault.delegate import (
    DelegateError,
    add_delegate,
    remove_delegate,
    resolve_delegate,
    list_delegates,
)


def _base_data():
    return {"vars": {"A": "alpha", "B": "beta", "C": "gamma"}}


def _make_load(data):
    def _load(_name):
        return data
    return _load


def _make_save(data):
    def _save(_name, d):
        data.clear()
        data.update(d)
    return _save


def test_add_delegate_stores_entry():
    data = _base_data()
    add_delegate("v", "A", "B", load=_make_load(data), save=_make_save(data))
    assert data["__delegates__"]["A"]["target"] == "B"


def test_add_delegate_with_description():
    data = _base_data()
    add_delegate("v", "A", "B", description="proxy", load=_make_load(data), save=_make_save(data))
    assert data["__delegates__"]["A"]["description"] == "proxy"


def test_add_delegate_missing_key_raises():
    data = _base_data()
    with pytest.raises(DelegateError, match="Key 'X'"):
        add_delegate("v", "X", "B", load=_make_load(data), save=_make_save(data))


def test_add_delegate_missing_target_raises():
    data = _base_data()
    with pytest.raises(DelegateError, match="Target key 'Z'"):
        add_delegate("v", "A", "Z", load=_make_load(data), save=_make_save(data))


def test_add_self_delegation_raises():
    data = _base_data()
    with pytest.raises(DelegateError, match="itself"):
        add_delegate("v", "A", "A", load=_make_load(data), save=_make_save(data))


def test_remove_delegate_removes_entry():
    data = _base_data()
    add_delegate("v", "A", "B", load=_make_load(data), save=_make_save(data))
    remove_delegate("v", "A", load=_make_load(data), save=_make_save(data))
    assert "A" not in data.get("__delegates__", {})


def test_remove_delegate_missing_raises():
    data = _base_data()
    with pytest.raises(DelegateError, match="No delegation"):
        remove_delegate("v", "A", load=_make_load(data), save=_make_save(data))


def test_resolve_delegate_returns_target_value():
    data = _base_data()
    add_delegate("v", "A", "B", load=_make_load(data), save=_make_save(data))
    result = resolve_delegate("v", "A", load=_make_load(data))
    assert result == "beta"


def test_resolve_delegate_no_delegation_returns_own_value():
    data = _base_data()
    result = resolve_delegate("v", "A", load=_make_load(data))
    assert result == "alpha"


def test_resolve_delegate_chain():
    data = _base_data()
    save = _make_save(data)
    load = _make_load(data)
    add_delegate("v", "A", "B", load=load, save=save)
    add_delegate("v", "B", "C", load=load, save=save)
    result = resolve_delegate("v", "A", load=load)
    assert result == "gamma"


def test_resolve_delegate_cycle_raises():
    data = _base_data()
    # Manually inject a cycle
    data.setdefault("__delegates__", {})
    data["__delegates__"]["A"] = {"target": "B"}
    data["__delegates__"]["B"] = {"target": "A"}
    with pytest.raises(DelegateError, match="cycle"):
        resolve_delegate("v", "A", load=_make_load(data))


def test_list_delegates_returns_entries():
    data = _base_data()
    add_delegate("v", "A", "B", description="d1", load=_make_load(data), save=_make_save(data))
    entries = list_delegates("v", load=_make_load(data))
    assert len(entries) == 1
    assert entries[0].key == "A"
    assert entries[0].target == "B"
    assert entries[0].description == "d1"


def test_list_delegates_empty():
    data = _base_data()
    entries = list_delegates("v", load=_make_load(data))
    assert entries == []
