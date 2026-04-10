"""Tests for env_vault.lint."""

import pytest

from env_vault.lint import (
    MAX_KEY_LENGTH,
    MAX_VALUE_LENGTH,
    LintWarning,
    lint_vars,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _severities(findings):
    return [f.severity for f in findings]


def _messages(findings):
    return [f.message for f in findings]


# ---------------------------------------------------------------------------
# clean input
# ---------------------------------------------------------------------------

def test_clean_vars_produce_no_findings():
    findings = lint_vars({"DATABASE_URL": "postgres://localhost/db", "PORT": "5432"})
    assert findings == []


# ---------------------------------------------------------------------------
# key naming
# ---------------------------------------------------------------------------

def test_lowercase_key_flagged():
    findings = lint_vars({"db_host": "localhost"})
    assert len(findings) == 1
    assert findings[0].severity == "warning"
    assert "POSIX" in findings[0].message


def test_key_with_leading_digit_flagged():
    findings = lint_vars({"1BAD": "value"})
    keys_flagged = [f.key for f in findings]
    assert "1BAD" in keys_flagged


def test_strict_keys_false_skips_naming_check():
    findings = lint_vars({"lower_case": "ok"}, strict_keys=False)
    assert all("POSIX" not in f.message for f in findings)


def test_key_too_long_is_error():
    long_key = "A" * (MAX_KEY_LENGTH + 1)
    findings = lint_vars({long_key: "value"})
    errors = [f for f in findings if f.severity == "error"]
    assert any("Key exceeds" in f.message for f in errors)


def test_key_exactly_max_length_is_ok():
    key = "A" * MAX_KEY_LENGTH
    findings = lint_vars({key: "value"})
    assert not any("Key exceeds" in f.message for f in findings)


# ---------------------------------------------------------------------------
# empty values
# ---------------------------------------------------------------------------

def test_empty_value_flagged():
    findings = lint_vars({"EMPTY_VAR": ""})
    assert any("empty" in f.message.lower() for f in findings)


def test_empty_value_warning_disabled():
    findings = lint_vars({"EMPTY_VAR": ""}, warn_empty_values=False)
    assert not any("empty" in f.message.lower() for f in findings)


# ---------------------------------------------------------------------------
# long values
# ---------------------------------------------------------------------------

def test_long_value_flagged():
    findings = lint_vars({"BIG": "x" * (MAX_VALUE_LENGTH + 1)})
    assert any("Value exceeds" in f.message for f in findings)


def test_long_value_warning_disabled():
    findings = lint_vars({"BIG": "x" * (MAX_VALUE_LENGTH + 1)}, warn_long_values=False)
    assert not any("Value exceeds" in f.message for f in findings)


def test_value_exactly_max_length_is_ok():
    findings = lint_vars({"OK": "x" * MAX_VALUE_LENGTH})
    assert not any("Value exceeds" in f.message for f in findings)


# ---------------------------------------------------------------------------
# multiple findings on same key
# ---------------------------------------------------------------------------

def test_multiple_findings_for_one_key():
    # lowercase (POSIX) + empty value -> two findings for the same key
    findings = lint_vars({"bad_key": ""})
    affected = [f for f in findings if f.key == "bad_key"]
    assert len(affected) >= 2


# ---------------------------------------------------------------------------
# LintWarning equality
# ---------------------------------------------------------------------------

def test_lint_warning_equality():
    a = LintWarning("KEY", "msg", "warning")
    b = LintWarning("KEY", "msg", "warning")
    assert a == b


def test_lint_warning_inequality():
    a = LintWarning("KEY", "msg", "warning")
    b = LintWarning("KEY", "msg", "error")
    assert a != b
