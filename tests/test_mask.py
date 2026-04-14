"""Tests for env_vault.mask."""

import pytest

from env_vault.mask import MaskError, MaskResult, mask_value, mask_vars


# ---------------------------------------------------------------------------
# mask_value
# ---------------------------------------------------------------------------

def test_mask_value_hides_prefix():
    result = mask_value("supersecret", reveal_chars=4)
    assert result.endswith("cret")
    assert result.startswith("*")


def test_mask_value_correct_length():
    value = "abcdefgh"
    result = mask_value(value, reveal_chars=2)
    assert len(result) == len(value)


def test_mask_value_fully_hidden():
    result = mask_value("password", fully_hidden=True)
    assert set(result) == {"*"}
    assert len(result) == len("password")


def test_mask_value_empty_string_fully_hidden_uses_minimum_length():
    result = mask_value("", fully_hidden=True)
    assert result == "*" * 8


def test_mask_value_reveal_chars_exceeds_length_reveals_nothing():
    result = mask_value("hi", reveal_chars=10)
    assert result == "**"


def test_mask_value_custom_mask_char():
    result = mask_value("abcdef", reveal_chars=2, mask_char="#")
    assert result == "####ef"


def test_mask_value_zero_reveal_chars():
    result = mask_value("secret", reveal_chars=0)
    assert result == "*" * 6


def test_mask_value_non_string_raises():
    with pytest.raises(MaskError, match="string"):
        mask_value(12345)  # type: ignore[arg-type]


def test_mask_value_invalid_mask_char_raises():
    with pytest.raises(MaskError, match="single character"):
        mask_value("abc", mask_char="**")


def test_mask_value_negative_reveal_chars_raises():
    with pytest.raises(MaskError, match=">= 0"):
        mask_value("abc", reveal_chars=-1)


# ---------------------------------------------------------------------------
# mask_vars
# ---------------------------------------------------------------------------

_VARS = {
    "DB_PASSWORD": "hunter2",
    "API_KEY": "abc123xyz",
    "HOST": "localhost",
}


def test_mask_vars_returns_all_keys_by_default():
    results = mask_vars(_VARS)
    assert set(results.keys()) == set(_VARS.keys())


def test_mask_vars_result_type():
    results = mask_vars(_VARS)
    for result in results.values():
        assert isinstance(result, MaskResult)


def test_mask_vars_original_preserved():
    results = mask_vars(_VARS)
    assert results["DB_PASSWORD"].original == "hunter2"


def test_mask_vars_masked_differs_from_original():
    results = mask_vars({"KEY": "longenoughvalue"}, reveal_chars=4)
    assert results["KEY"].masked != results["KEY"].original


def test_mask_vars_specific_keys():
    results = mask_vars(_VARS, keys=["API_KEY"])
    assert set(results.keys()) == {"API_KEY"}


def test_mask_vars_unknown_key_raises():
    with pytest.raises(MaskError, match="MISSING"):
        mask_vars(_VARS, keys=["MISSING"])


def test_mask_vars_fully_hidden_flag():
    results = mask_vars({"TOKEN": "secrettoken"}, fully_hidden=True)
    assert results["TOKEN"].fully_hidden is True
    assert set(results["TOKEN"].masked) == {"*"}


def test_mask_vars_repr_contains_key():
    results = mask_vars({"X": "value"}, reveal_chars=2)
    assert "X" in repr(results["X"])
