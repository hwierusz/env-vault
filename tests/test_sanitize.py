"""Tests for env_vault.sanitize."""

import pytest

from env_vault.sanitize import (
    SanitizeError,
    find_dirty_keys,
    sanitize_entry,
    sanitize_key,
    sanitize_value,
    sanitize_vars,
)


# ---------------------------------------------------------------------------
# sanitize_key
# ---------------------------------------------------------------------------

def test_sanitize_key_uppercases():
    assert sanitize_key("my_var") == "MY_VAR"


def test_sanitize_key_replaces_hyphen():
    assert sanitize_key("MY-VAR") == "MY_VAR"


def test_sanitize_key_replaces_space():
    assert sanitize_key("MY VAR") == "MY_VAR"


def test_sanitize_key_prepends_underscore_for_leading_digit():
    assert sanitize_key("1VAR") == "_1VAR"


def test_sanitize_key_already_clean():
    assert sanitize_key("DATABASE_URL") == "DATABASE_URL"


# ---------------------------------------------------------------------------
# sanitize_value
# ---------------------------------------------------------------------------

def test_sanitize_value_strips_whitespace():
    assert sanitize_value("  hello  ") == "hello"


def test_sanitize_value_removes_null_bytes():
    assert sanitize_value("val\x00ue") == "value"


def test_sanitize_value_already_clean():
    assert sanitize_value("production") == "production"


# ---------------------------------------------------------------------------
# sanitize_entry
# ---------------------------------------------------------------------------

def test_sanitize_entry_flags_key_changed():
    result = sanitize_entry("my-var", "hello")
    assert result.key_changed is True
    assert result.key == "MY_VAR"


def test_sanitize_entry_flags_value_changed():
    result = sanitize_entry("MY_VAR", "  hello  ")
    assert result.value_changed is True
    assert result.value == "hello"


def test_sanitize_entry_no_changes():
    result = sanitize_entry("MY_VAR", "hello")
    assert result.key_changed is False
    assert result.value_changed is False


# ---------------------------------------------------------------------------
# sanitize_vars
# ---------------------------------------------------------------------------

def test_sanitize_vars_basic():
    out = sanitize_vars({"my-var": "  world  ", "DB_URL": "postgres://localhost"})
    assert out == {"MY_VAR": "world", "DB_URL": "postgres://localhost"}


def test_sanitize_vars_strict_raises_on_dirty_key():
    with pytest.raises(SanitizeError, match="not valid"):
        sanitize_vars({"bad-key": "value"}, strict=True)


def test_sanitize_vars_strict_passes_clean_keys():
    out = sanitize_vars({"GOOD_KEY": "value"}, strict=True)
    assert out == {"GOOD_KEY": "value"}


def test_sanitize_vars_collision_raises():
    # Both "my-var" and "MY_VAR" sanitize to "MY_VAR"
    with pytest.raises(SanitizeError, match="collision"):
        sanitize_vars({"my-var": "a", "MY_VAR": "b"})


# ---------------------------------------------------------------------------
# find_dirty_keys
# ---------------------------------------------------------------------------

def test_find_dirty_keys_returns_only_dirty():
    dirty = find_dirty_keys({"good_key": "v", "bad-key": "v", "ALSO_GOOD": "v"})
    assert dirty == ["bad-key"]


def test_find_dirty_keys_empty_when_all_clean():
    assert find_dirty_keys({"A": "1", "B_C": "2"}) == []
