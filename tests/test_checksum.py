"""Tests for env_vault.checksum module."""

import pytest

from env_vault.checksum import (
    ChecksumError,
    checksum_diff,
    compute_checksum,
    verify_checksum,
)


VARS = {"API_KEY": "secret", "DB_HOST": "localhost", "PORT": "5432"}


def test_compute_checksum_returns_hex_string():
    result = compute_checksum(VARS)
    assert isinstance(result, str)
    assert len(result) == 64  # sha256 hex digest length


def test_compute_checksum_is_deterministic():
    assert compute_checksum(VARS) == compute_checksum(VARS)


def test_compute_checksum_order_independent():
    shuffled = {"PORT": "5432", "API_KEY": "secret", "DB_HOST": "localhost"}
    assert compute_checksum(VARS) == compute_checksum(shuffled)


def test_compute_checksum_changes_on_value_change():
    modified = dict(VARS)
    modified["PORT"] = "9999"
    assert compute_checksum(VARS) != compute_checksum(modified)


def test_compute_checksum_changes_on_key_added():
    extended = dict(VARS)
    extended["NEW_VAR"] = "value"
    assert compute_checksum(VARS) != compute_checksum(extended)


def test_compute_checksum_empty_dict():
    result = compute_checksum({})
    assert isinstance(result, str)
    assert len(result) == 64


def test_compute_checksum_sha1_algorithm():
    result = compute_checksum(VARS, algorithm="sha1")
    assert len(result) == 40  # sha1 hex digest length


def test_compute_checksum_unsupported_algorithm_raises():
    with pytest.raises(ChecksumError, match="Unsupported hash algorithm"):
        compute_checksum(VARS, algorithm="rot13")


def test_verify_checksum_returns_true_for_matching():
    cs = compute_checksum(VARS)
    assert verify_checksum(VARS, cs) is True


def test_verify_checksum_returns_false_for_mismatch():
    cs = compute_checksum(VARS)
    modified = dict(VARS)
    modified["API_KEY"] = "different"
    assert verify_checksum(modified, cs) is False


def test_verify_checksum_empty_dict():
    cs = compute_checksum({})
    assert verify_checksum({}, cs) is True


def test_checksum_diff_returns_none_when_identical():
    assert checksum_diff(VARS, dict(VARS)) is None


def test_checksum_diff_returns_new_checksum_when_different():
    modified = dict(VARS)
    modified["PORT"] = "8080"
    result = checksum_diff(VARS, modified)
    assert result is not None
    assert result == compute_checksum(modified)


def test_checksum_diff_both_empty_returns_none():
    assert checksum_diff({}, {}) is None
