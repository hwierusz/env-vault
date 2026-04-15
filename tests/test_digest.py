"""Tests for env_vault.digest."""
from __future__ import annotations

import pytest

from env_vault.digest import (
    DigestError,
    compute_digest,
    digest_changed,
    verify_digest,
)

VARS = {"DB_HOST": "localhost", "DB_PORT": "5432"}
SECRET = "supersecret"


# ---------------------------------------------------------------------------
# compute_digest
# ---------------------------------------------------------------------------

def test_compute_digest_returns_hex_string():
    result = compute_digest(VARS, SECRET)
    assert isinstance(result, str)
    assert len(result) == 64
    assert all(c in "0123456789abcdef" for c in result)


def test_compute_digest_is_deterministic():
    assert compute_digest(VARS, SECRET) == compute_digest(VARS, SECRET)


def test_compute_digest_order_independent():
    vars_a = {"A": "1", "B": "2"}
    vars_b = {"B": "2", "A": "1"}
    assert compute_digest(vars_a, SECRET) == compute_digest(vars_b, SECRET)


def test_compute_digest_changes_on_value_change():
    modified = {**VARS, "DB_PORT": "9999"}
    assert compute_digest(VARS, SECRET) != compute_digest(modified, SECRET)


def test_compute_digest_changes_on_key_added():
    extended = {**VARS, "NEW_KEY": "value"}
    assert compute_digest(VARS, SECRET) != compute_digest(extended, SECRET)


def test_compute_digest_different_secrets_differ():
    assert compute_digest(VARS, "secret1") != compute_digest(VARS, "secret2")


def test_compute_digest_empty_vars_ok():
    result = compute_digest({}, SECRET)
    assert len(result) == 64


def test_compute_digest_raises_for_non_dict():
    with pytest.raises(DigestError, match="dict"):
        compute_digest(["A=1"], SECRET)  # type: ignore[arg-type]


def test_compute_digest_raises_for_empty_secret():
    with pytest.raises(DigestError, match="empty"):
        compute_digest(VARS, "")


# ---------------------------------------------------------------------------
# verify_digest
# ---------------------------------------------------------------------------

def test_verify_digest_returns_true_for_correct_digest():
    stored = compute_digest(VARS, SECRET)
    assert verify_digest(VARS, SECRET, stored) is True


def test_verify_digest_returns_false_for_tampered_vars():
    stored = compute_digest(VARS, SECRET)
    tampered = {**VARS, "DB_HOST": "evil-host"}
    assert verify_digest(tampered, SECRET, stored) is False


def test_verify_digest_case_insensitive_expected():
    stored = compute_digest(VARS, SECRET).upper()
    assert verify_digest(VARS, SECRET, stored) is True


# ---------------------------------------------------------------------------
# digest_changed
# ---------------------------------------------------------------------------

def test_digest_changed_false_when_unchanged():
    stored = compute_digest(VARS, SECRET)
    assert digest_changed(VARS, SECRET, stored) is False


def test_digest_changed_true_when_modified():
    stored = compute_digest(VARS, SECRET)
    modified = {**VARS, "EXTRA": "yes"}
    assert digest_changed(modified, SECRET, stored) is True
