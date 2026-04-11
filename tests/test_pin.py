"""Tests for env_vault.pin module."""

from __future__ import annotations

import pytest

from env_vault.pin import (
    PIN_STORE_KEY,
    PinError,
    list_pinned_keys,
    remove_pin,
    set_pin,
    verify_pin,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_load(data: dict):
    def _load(vault_name):
        return dict(data)
    return _load


def _make_save(captured: list):
    def _save(vault_name, data):
        captured.append(dict(data))
    return _save


BASE_DATA = {"API_KEY": "secret", "DB_PASS": "hunter2"}


# ---------------------------------------------------------------------------
# set_pin
# ---------------------------------------------------------------------------

def test_set_pin_stores_hash():
    saved = []
    set_pin("myapp", "API_KEY", "1234", _make_load(BASE_DATA), _make_save(saved))
    assert PIN_STORE_KEY in saved[0]
    assert "API_KEY" in saved[0][PIN_STORE_KEY]


def test_set_pin_raises_for_non_digit_pin():
    with pytest.raises(PinError, match="digits only"):
        set_pin("myapp", "API_KEY", "abcd", _make_load(BASE_DATA), _make_save([]))


def test_set_pin_raises_for_short_pin():
    with pytest.raises(PinError, match="at least 4"):
        set_pin("myapp", "API_KEY", "12", _make_load(BASE_DATA), _make_save([]))


def test_set_pin_raises_for_missing_key():
    with pytest.raises(PinError, match="not found"):
        set_pin("myapp", "MISSING", "1234", _make_load(BASE_DATA), _make_save([]))


# ---------------------------------------------------------------------------
# remove_pin
# ---------------------------------------------------------------------------

def test_remove_pin_deletes_entry():
    data = dict(BASE_DATA)
    data[PIN_STORE_KEY] = {"API_KEY": "somehash"}
    saved = []
    remove_pin("myapp", "API_KEY", _make_load(data), _make_save(saved))
    assert "API_KEY" not in saved[0][PIN_STORE_KEY]


def test_remove_pin_raises_if_no_pin_set():
    with pytest.raises(PinError, match="No PIN set"):
        remove_pin("myapp", "API_KEY", _make_load(BASE_DATA), _make_save([]))


# ---------------------------------------------------------------------------
# verify_pin
# ---------------------------------------------------------------------------

def test_verify_pin_correct():
    saved = []
    set_pin("myapp", "API_KEY", "9999", _make_load(BASE_DATA), _make_save(saved))
    stored = saved[0]
    assert verify_pin("myapp", "API_KEY", "9999", _make_load(stored)) is True


def test_verify_pin_incorrect():
    saved = []
    set_pin("myapp", "API_KEY", "9999", _make_load(BASE_DATA), _make_save(saved))
    stored = saved[0]
    assert verify_pin("myapp", "API_KEY", "0000", _make_load(stored)) is False


def test_verify_pin_no_pin_set_returns_true():
    """Keys without a PIN should always pass verification."""
    assert verify_pin("myapp", "API_KEY", "", _make_load(BASE_DATA)) is True


# ---------------------------------------------------------------------------
# list_pinned_keys
# ---------------------------------------------------------------------------

def test_list_pinned_keys_returns_keys():
    data = dict(BASE_DATA)
    data[PIN_STORE_KEY] = {"API_KEY": "h1", "DB_PASS": "h2"}
    keys = list_pinned_keys("myapp", _make_load(data))
    assert set(keys) == {"API_KEY", "DB_PASS"}


def test_list_pinned_keys_empty_when_none_set():
    keys = list_pinned_keys("myapp", _make_load(BASE_DATA))
    assert keys == []
