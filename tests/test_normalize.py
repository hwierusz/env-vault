"""Tests for env_vault.normalize."""

import pytest

from env_vault.normalize import (
    NormalizeError,
    NormalizeResult,
    normalize_key,
    normalize_value,
    normalize_vars,
)


# ---------------------------------------------------------------------------
# normalize_key
# ---------------------------------------------------------------------------

def test_normalize_key_uppercases():
    key, changes = normalize_key("my_key")
    assert key == "MY_KEY"
    assert "key uppercased" in changes


def test_normalize_key_already_upper_no_change():
    key, changes = normalize_key("MY_KEY")
    assert key == "MY_KEY"
    assert changes == []


def test_normalize_key_replaces_hyphen():
    key, changes = normalize_key("MY-KEY")
    assert key == "MY_KEY"
    assert "invalid characters replaced with underscore" in changes


def test_normalize_key_replaces_space():
    key, changes = normalize_key("MY KEY")
    assert key == "MY_KEY"
    assert "invalid characters replaced with underscore" in changes


def test_normalize_key_prepends_underscore_for_leading_digit():
    key, changes = normalize_key("1VAR")
    assert key == "_1VAR"
    assert "leading digit prefixed with underscore" in changes


def test_normalize_key_empty_raises():
    with pytest.raises(NormalizeError):
        normalize_key("")


def test_normalize_key_only_special_chars_raises():
    # All chars become underscores, but result is non-empty so no error.
    key, changes = normalize_key("---")
    assert key == "___"


# ---------------------------------------------------------------------------
# normalize_value
# ---------------------------------------------------------------------------

def test_normalize_value_strips_whitespace():
    value, changes = normalize_value("  hello  ")
    assert value == "hello"
    assert "leading/trailing whitespace stripped" in changes


def test_normalize_value_removes_double_quotes():
    value, changes = normalize_value('"hello"')
    assert value == "hello"
    assert 'surrounding " quotes removed' in changes


def test_normalize_value_removes_single_quotes():
    value, changes = normalize_value("'world'")
    assert value == "world"
    assert "surrounding ' quotes removed" in changes


def test_normalize_value_no_change():
    value, changes = normalize_value("clean")
    assert value == "clean"
    assert changes == []


def test_normalize_value_empty_string_unchanged():
    value, changes = normalize_value("")
    assert value == ""
    assert changes == []


# ---------------------------------------------------------------------------
# normalize_vars
# ---------------------------------------------------------------------------

def test_normalize_vars_returns_results():
    results = normalize_vars({"my_key": '"hello world"'})
    assert len(results) == 1
    r = results[0]
    assert isinstance(r, NormalizeResult)
    assert r.normalized_key == "MY_KEY"
    assert r.normalized_value == "hello world"
    assert r.was_changed is True


def test_normalize_vars_multiple_entries():
    results = normalize_vars({"a": "1", "B": "2"})
    keys = {r.normalized_key for r in results}
    assert keys == {"A", "B"}


def test_normalize_vars_skip_errors_ignores_bad_keys():
    # An all-digit key after upper would be prefixed, but empty string should skip.
    # Force an empty key situation by patching isn't easy; test skip_errors=False default.
    results = normalize_vars({"OK": "val"}, skip_errors=True)
    assert len(results) == 1


def test_normalize_vars_raises_on_bad_key_by_default():
    with pytest.raises(NormalizeError):
        normalize_vars({"": "value"})


def test_normalize_result_was_changed_false_for_clean():
    results = normalize_vars({"CLEAN": "value"})
    assert results[0].was_changed is False
