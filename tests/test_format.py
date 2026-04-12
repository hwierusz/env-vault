"""Tests for env_vault.format."""

from __future__ import annotations

import pytest

from env_vault.format import (
    FormatError,
    available_formats,
    format_value,
    format_vars,
)


# ---------------------------------------------------------------------------
# available_formats
# ---------------------------------------------------------------------------

def test_available_formats_returns_list():
    result = available_formats()
    assert isinstance(result, list)
    assert len(result) > 0


def test_available_formats_includes_builtins():
    fmts = available_formats()
    for name in ("upper", "lower", "strip", "base64", "sha256"):
        assert name in fmts


def test_available_formats_is_sorted():
    fmts = available_formats()
    assert fmts == sorted(fmts)


# ---------------------------------------------------------------------------
# format_value
# ---------------------------------------------------------------------------

def test_format_value_upper():
    assert format_value("hello", "upper") == "HELLO"


def test_format_value_lower():
    assert format_value("WORLD", "lower") == "world"


def test_format_value_strip():
    assert format_value("  spaces  ", "strip") == "spaces"


def test_format_value_title():
    assert format_value("hello world", "title") == "Hello World"


def test_format_value_reverse():
    assert format_value("abc", "reverse") == "cba"


def test_format_value_base64_roundtrip():
    original = "secret_value"
    encoded = format_value(original, "base64")
    assert format_value(encoded, "base64decode") == original


def test_format_value_urlencode_roundtrip():
    original = "hello world/path"
    encoded = format_value(original, "urlencode")
    assert " " not in encoded
    assert format_value(encoded, "urldecode") == original


def test_format_value_len():
    assert format_value("hello", "len") == "5"


def test_format_value_hex():
    result = format_value("hi", "hex")
    assert result == "6869"


def test_format_value_sha256_returns_64_hex_chars():
    result = format_value("password", "sha256")
    assert len(result) == 64
    assert all(c in "0123456789abcdef" for c in result)


def test_format_value_sha256_is_deterministic():
    assert format_value("same", "sha256") == format_value("same", "sha256")


def test_format_value_unknown_raises():
    with pytest.raises(FormatError, match="Unknown format"):
        format_value("value", "nonexistent_fmt")


# ---------------------------------------------------------------------------
# format_vars
# ---------------------------------------------------------------------------

def test_format_vars_applies_to_all():
    vars_ = {"A": "hello", "B": "world"}
    result = format_vars(vars_, "upper")
    assert result == {"A": "HELLO", "B": "WORLD"}


def test_format_vars_does_not_mutate_original():
    vars_ = {"A": "hello"}
    format_vars(vars_, "upper")
    assert vars_["A"] == "hello"


def test_format_vars_restricted_to_keys():
    vars_ = {"A": "hello", "B": "world"}
    result = format_vars(vars_, "upper", keys=["A"])
    assert result["A"] == "HELLO"
    assert result["B"] == "world"


def test_format_vars_missing_key_raises():
    vars_ = {"A": "hello"}
    with pytest.raises(FormatError, match="not found in vault"):
        format_vars(vars_, "upper", keys=["MISSING"])


def test_format_vars_unknown_format_raises():
    with pytest.raises(FormatError, match="Unknown format"):
        format_vars({"A": "v"}, "bogus")
