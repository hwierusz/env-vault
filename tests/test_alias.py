"""Tests for env_vault.alias."""

import pytest

from env_vault.alias import (
    AliasError,
    add_alias,
    list_aliases,
    remove_alias,
    resolve_alias,
)

_VAULT = "test_vault"
_PASS = "secret"


def _make_load(data: dict):
    def _load(vault, password):
        return dict(data)
    return _load


def _make_save():
    saved = {}

    def _save(vault, password, data):
        saved.update(data)

    _save.saved = saved
    return _save


@pytest.fixture
def base_data():
    return {"DB_HOST": "localhost", "DB_PORT": "5432"}


def test_add_alias_stores_mapping(base_data):
    saver = _make_save()
    add_alias(_VAULT, _PASS, "host", "DB_HOST",
              load_fn=_make_load(base_data), save_fn=saver)
    assert saver.saved["__aliases__"]["host"] == "DB_HOST"


def test_add_alias_invalid_name_raises(base_data):
    with pytest.raises(AliasError, match="Invalid alias"):
        add_alias(_VAULT, _PASS, "bad-name!", "DB_HOST",
                  load_fn=_make_load(base_data), save_fn=_make_save())


def test_add_alias_missing_target_raises(base_data):
    with pytest.raises(AliasError, match="does not exist"):
        add_alias(_VAULT, _PASS, "ghost", "MISSING_KEY",
                  load_fn=_make_load(base_data), save_fn=_make_save())


def test_remove_alias_deletes_entry():
    data = {"DB_HOST": "localhost", "__aliases__": {"host": "DB_HOST"}}
    saver = _make_save()
    remove_alias(_VAULT, _PASS, "host",
                 load_fn=_make_load(data), save_fn=saver)
    assert "host" not in saver.saved.get("__aliases__", {})


def test_remove_alias_not_found_raises():
    data = {"DB_HOST": "localhost", "__aliases__": {}}
    with pytest.raises(AliasError, match="not found"):
        remove_alias(_VAULT, _PASS, "ghost",
                     load_fn=_make_load(data), save_fn=_make_save())


def test_resolve_alias_returns_key():
    data = {"DB_HOST": "localhost", "__aliases__": {"host": "DB_HOST"}}
    result = resolve_alias(_VAULT, _PASS, "host", load_fn=_make_load(data))
    assert result == "DB_HOST"


def test_resolve_alias_unknown_returns_none():
    data = {"DB_HOST": "localhost", "__aliases__": {}}
    result = resolve_alias(_VAULT, _PASS, "nope", load_fn=_make_load(data))
    assert result is None


def test_list_aliases_returns_all():
    data = {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "__aliases__": {"host": "DB_HOST", "port": "DB_PORT"},
    }
    aliases = list_aliases(_VAULT, _PASS, load_fn=_make_load(data))
    assert aliases == {"host": "DB_HOST", "port": "DB_PORT"}


def test_list_aliases_empty_when_none():
    data = {"DB_HOST": "localhost"}
    aliases = list_aliases(_VAULT, _PASS, load_fn=_make_load(data))
    assert aliases == {}
