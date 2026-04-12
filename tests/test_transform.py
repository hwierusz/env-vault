"""Tests for env_vault.transform."""

import pytest

from env_vault.transform import (
    TransformError,
    apply_transform,
    apply_transforms,
    available_transforms,
    transform_vars,
)


def test_available_transforms_returns_list():
    names = available_transforms()
    assert isinstance(names, list)
    assert len(names) > 0


def test_available_transforms_includes_builtins():
    names = available_transforms()
    for expected in ("upper", "lower", "strip", "mask", "base64_encode", "base64_decode"):
        assert expected in names


def test_upper_transform():
    assert apply_transform("hello", "upper") == "HELLO"


def test_lower_transform():
    assert apply_transform("WORLD", "lower") == "world"


def test_strip_transform():
    assert apply_transform("  spaced  ", "strip") == "spaced"


def test_strip_quotes_double():
    assert apply_transform('"quoted"', "strip_quotes") == "quoted"


def test_strip_quotes_single():
    assert apply_transform("'quoted'", "strip_quotes") == "quoted"


def test_strip_quotes_no_quotes():
    assert apply_transform("plain", "strip_quotes") == "plain"


def test_mask_long_value():
    result = apply_transform("supersecret", "mask")
    assert result.startswith("su")
    assert result.endswith("et")
    assert "*" in result


def test_mask_short_value():
    result = apply_transform("ab", "mask")
    assert result == "**"


def test_base64_roundtrip():
    encoded = apply_transform("my_secret", "base64_encode")
    decoded = apply_transform(encoded, "base64_decode")
    assert decoded == "my_secret"


def test_base64_decode_invalid_raises():
    with pytest.raises(TransformError, match="base64_decode failed"):
        apply_transform("!!!not_base64!!!", "base64_decode")


def test_unknown_transform_raises():
    with pytest.raises(TransformError, match="Unknown transform"):
        apply_transform("value", "nonexistent")


def test_apply_transforms_chain():
    result = apply_transforms("  hello  ", ["strip", "upper"])
    assert result == "HELLO"


def test_apply_transforms_empty_list():
    assert apply_transforms("unchanged", []) == "unchanged"


def test_transform_vars_all_keys():
    variables = {"A": "hello", "B": "world"}
    result = transform_vars(variables, ["upper"])
    assert result == {"A": "HELLO", "B": "WORLD"}


def test_transform_vars_specific_keys():
    variables = {"A": "hello", "B": "world"}
    result = transform_vars(variables, ["upper"], keys=["A"])
    assert result["A"] == "HELLO"
    assert result["B"] == "world"


def test_transform_vars_returns_new_dict():
    variables = {"X": "value"}
    result = transform_vars(variables, ["upper"])
    assert result is not variables


def test_transform_vars_unknown_key_in_keys_list_ignored():
    variables = {"A": "hello"}
    result = transform_vars(variables, ["upper"], keys=["A", "MISSING"])
    assert result == {"A": "HELLO"}
