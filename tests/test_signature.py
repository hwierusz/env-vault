"""Tests for env_vault.signature."""
from __future__ import annotations

import pytest

from env_vault.signature import (
    SignatureError,
    attach_signature,
    check_signature,
    sign_vault,
    verify_signature,
)

VARS = {"DB_HOST": "localhost", "DB_PORT": "5432"}
SECRET = "supersecret"


def test_sign_vault_returns_hex_string():
    sig = sign_vault(VARS, SECRET)
    assert isinstance(sig, str)
    assert len(sig) == 64  # SHA-256 hex


def test_sign_vault_is_deterministic():
    assert sign_vault(VARS, SECRET) == sign_vault(VARS, SECRET)


def test_sign_vault_order_independent():
    v1 = {"A": "1", "B": "2"}
    v2 = {"B": "2", "A": "1"}
    assert sign_vault(v1, SECRET) == sign_vault(v2, SECRET)


def test_sign_vault_changes_on_value_change():
    modified = dict(VARS, DB_HOST="remotehost")
    assert sign_vault(VARS, SECRET) != sign_vault(modified, SECRET)


def test_sign_vault_empty_secret_raises():
    with pytest.raises(SignatureError):
        sign_vault(VARS, "")


def test_verify_signature_true_for_valid():
    sig = sign_vault(VARS, SECRET)
    assert verify_signature(VARS, SECRET, sig) is True


def test_verify_signature_false_for_tampered_vars():
    sig = sign_vault(VARS, SECRET)
    tampered = dict(VARS, DB_HOST="evil")
    assert verify_signature(tampered, SECRET, sig) is False


def test_verify_signature_false_for_wrong_secret():
    sig = sign_vault(VARS, SECRET)
    assert verify_signature(VARS, "wrongsecret", sig) is False


def test_attach_signature_stores_in_meta():
    data = {"vars": VARS}
    signed = attach_signature(data, SECRET)
    assert "signature" in signed["__meta__"]


def test_attach_signature_preserves_existing_meta():
    data = {"vars": VARS, "__meta__": {"created": "2024-01-01"}}
    signed = attach_signature(data, SECRET)
    assert signed["__meta__"]["created"] == "2024-01-01"
    assert "signature" in signed["__meta__"]


def test_check_signature_valid():
    data = attach_signature({"vars": VARS}, SECRET)
    assert check_signature(data, SECRET) is True


def test_check_signature_invalid_after_tampering():
    data = attach_signature({"vars": VARS}, SECRET)
    data["vars"]["INJECTED"] = "bad"
    assert check_signature(data, SECRET) is False


def test_check_signature_raises_when_missing():
    data = {"vars": VARS}
    with pytest.raises(SignatureError, match="no signature"):
        check_signature(data, SECRET)
