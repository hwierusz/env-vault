"""Tests for env_vault.remind."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from env_vault.remind import RemindError, ReminderEntry, check_reminders

VAULT = "test_vault"
DATA = {"API_KEY": "secret", "DB_PASS": "hunter2", "TOKEN": "abc"}


def _make_load_fn(ttl_map):
    """Return a fake load_fn that stores TTL metadata."""
    now = time.time()

    def fake_get_ttl(vault_name, key, load_fn=None):
        offset = ttl_map.get(key)
        if offset is None:
            return None
        return now + offset

    return fake_get_ttl


# ---------------------------------------------------------------------------
# check_reminders
# ---------------------------------------------------------------------------

def test_returns_empty_when_no_ttls_set():
    with patch("env_vault.remind.get_ttl", return_value=None):
        result = check_reminders(VAULT, DATA)
    assert result == []


def test_returns_entry_for_expiring_key():
    now = time.time()
    with patch("env_vault.remind.get_ttl") as mock_get:
        mock_get.side_effect = lambda v, k, load_fn=None: (
            now + 3600 if k == "API_KEY" else None
        )
        result = check_reminders(VAULT, DATA, threshold_seconds=86400)

    assert len(result) == 1
    assert result[0].key == "API_KEY"
    assert not result[0].expired
    assert 3500 < result[0].seconds_remaining < 3700


def test_expired_key_flagged():
    now = time.time()
    with patch("env_vault.remind.get_ttl") as mock_get:
        mock_get.side_effect = lambda v, k, load_fn=None: (
            now - 60 if k == "TOKEN" else None
        )
        result = check_reminders(VAULT, DATA, threshold_seconds=86400)

    assert len(result) == 1
    entry = result[0]
    assert entry.key == "TOKEN"
    assert entry.expired
    assert entry.seconds_remaining == 0.0


def test_results_sorted_by_seconds_remaining():
    now = time.time()
    offsets = {"API_KEY": 100, "DB_PASS": 50, "TOKEN": 200}
    with patch("env_vault.remind.get_ttl") as mock_get:
        mock_get.side_effect = lambda v, k, load_fn=None: (
            now + offsets[k] if k in offsets else None
        )
        result = check_reminders(VAULT, DATA, threshold_seconds=86400)

    keys = [e.key for e in result]
    assert keys == ["DB_PASS", "API_KEY", "TOKEN"]


def test_key_beyond_threshold_excluded():
    now = time.time()
    with patch("env_vault.remind.get_ttl") as mock_get:
        mock_get.side_effect = lambda v, k, load_fn=None: (
            now + 90000 if k == "API_KEY" else None
        )
        result = check_reminders(VAULT, DATA, threshold_seconds=86400)

    assert result == []


def test_invalid_threshold_raises():
    with pytest.raises(RemindError):
        check_reminders(VAULT, DATA, threshold_seconds=0)


def test_negative_threshold_raises():
    with pytest.raises(RemindError):
        check_reminders(VAULT, DATA, threshold_seconds=-1)
