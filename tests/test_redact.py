"""Tests for env_vault.redact."""

import pytest

from env_vault.redact import (
    DEFAULT_MASK,
    RedactResult,
    is_sensitive,
    redact_value,
    redact_vars,
)


# ---------------------------------------------------------------------------
# is_sensitive
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key", [
    "DB_PASSWORD",
    "api_key",
    "AUTH_TOKEN",
    "PRIVATE_KEY",
    "secret",
    "AWS_SECRET_ACCESS_KEY",
    "PASSPHRASE",
    "user_credentials",
])
def test_is_sensitive_returns_true_for_sensitive_keys(key):
    assert is_sensitive(key) is True


@pytest.mark.parametrize("key", [
    "DATABASE_HOST",
    "PORT",
    "LOG_LEVEL",
    "APP_NAME",
])
def test_is_sensitive_returns_false_for_plain_keys(key):
    assert is_sensitive(key) is False


# ---------------------------------------------------------------------------
# redact_value
# ---------------------------------------------------------------------------

def test_redact_value_returns_mask_by_default():
    assert redact_value("supersecret") == DEFAULT_MASK


def test_redact_value_custom_mask():
    assert redact_value("supersecret", mask="[hidden]") == "[hidden]"


def test_redact_value_empty_string_returns_mask():
    assert redact_value("") == DEFAULT_MASK


def test_redact_value_partial_long_value():
    value = "abcdefghijklmnop"  # 16 chars
    result = redact_value(value, partial=True)
    assert result.startswith("abcd")
    assert result.endswith("mnop")
    assert "..." in result


def test_redact_value_partial_short_value_returns_mask():
    # 8 chars <= 4*2 => full mask
    assert redact_value("short123", partial=True) == DEFAULT_MASK


# ---------------------------------------------------------------------------
# redact_vars
# ---------------------------------------------------------------------------

def test_redact_vars_masks_sensitive_keys():
    variables = {"DB_PASSWORD": "hunter2", "HOST": "localhost"}
    results = {r.key: r for r in redact_vars(variables)}

    assert results["DB_PASSWORD"].was_redacted is True
    assert results["DB_PASSWORD"].redacted == DEFAULT_MASK
    assert results["DB_PASSWORD"].original == "hunter2"


def test_redact_vars_leaves_plain_keys_unchanged():
    variables = {"HOST": "localhost", "PORT": "5432"}
    results = {r.key: r for r in redact_vars(variables)}

    assert results["HOST"].was_redacted is False
    assert results["HOST"].redacted == "localhost"


def test_redact_vars_extra_keys_are_treated_as_sensitive():
    variables = {"MY_CUSTOM_FIELD": "topsecret", "OTHER": "value"}
    results = {r.key: r for r in redact_vars(variables, extra_keys=["MY_CUSTOM_FIELD"])}

    assert results["MY_CUSTOM_FIELD"].was_redacted is True


def test_redact_vars_returns_redact_result_instances():
    results = redact_vars({"KEY": "val"})
    assert all(isinstance(r, RedactResult) for r in results)


def test_redact_vars_empty_dict_returns_empty_list():
    assert redact_vars({}) == []
