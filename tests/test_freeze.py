"""Tests for env_vault.freeze."""

import pytest

from env_vault.freeze import FreezeError, freeze_vault, get_freeze_reason, is_frozen, unfreeze_vault


def _make_load(data_store: dict):
    def _load(vault_name):
        return data_store.get(vault_name)
    return _load


def _make_save(data_store: dict):
    def _save(vault_name, data):
        data_store[vault_name] = data
    return _save


@pytest.fixture()
def store():
    return {"myvault": {"vars": {"KEY": "value"}}}


def test_freeze_sets_frozen_flag(store):
    freeze_vault("myvault", load=_make_load(store), save=_make_save(store))
    assert store["myvault"]["__freeze__"]["frozen"] is True


def test_freeze_stores_reason(store):
    freeze_vault("myvault", reason="audit", load=_make_load(store), save=_make_save(store))
    assert store["myvault"]["__freeze__"]["reason"] == "audit"


def test_freeze_missing_vault_raises():
    store = {}
    with pytest.raises(FreezeError, match="does not exist"):
        freeze_vault("missing", load=_make_load(store), save=_make_save(store))


def test_freeze_already_frozen_raises(store):
    freeze_vault("myvault", load=_make_load(store), save=_make_save(store))
    with pytest.raises(FreezeError, match="already frozen"):
        freeze_vault("myvault", load=_make_load(store), save=_make_save(store))


def test_unfreeze_clears_flag(store):
    freeze_vault("myvault", load=_make_load(store), save=_make_save(store))
    unfreeze_vault("myvault", load=_make_load(store), save=_make_save(store))
    assert store["myvault"]["__freeze__"]["frozen"] is False


def test_unfreeze_not_frozen_raises(store):
    with pytest.raises(FreezeError, match="not frozen"):
        unfreeze_vault("myvault", load=_make_load(store), save=_make_save(store))


def test_unfreeze_missing_vault_raises():
    store = {}
    with pytest.raises(FreezeError, match="does not exist"):
        unfreeze_vault("missing", load=_make_load(store), save=_make_save(store))


def test_is_frozen_returns_true_after_freeze(store):
    freeze_vault("myvault", load=_make_load(store), save=_make_save(store))
    assert is_frozen("myvault", load=_make_load(store)) is True


def test_is_frozen_returns_false_before_freeze(store):
    assert is_frozen("myvault", load=_make_load(store)) is False


def test_is_frozen_returns_false_for_missing_vault():
    assert is_frozen("ghost", load=_make_load({})) is False


def test_get_freeze_reason_returns_reason(store):
    freeze_vault("myvault", reason="compliance", load=_make_load(store), save=_make_save(store))
    assert get_freeze_reason("myvault", load=_make_load(store)) == "compliance"


def test_get_freeze_reason_empty_when_not_frozen(store):
    assert get_freeze_reason("myvault", load=_make_load(store)) == ""


def test_get_freeze_reason_empty_for_missing_vault():
    assert get_freeze_reason("ghost", load=_make_load({})) == ""
