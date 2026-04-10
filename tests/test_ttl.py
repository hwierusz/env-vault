"""Tests for env_vault.ttl."""

import time
import pytest
from env_vault.ttl import (
    TTLError,
    TTL_META_KEY,
    set_ttl,
    get_ttl,
    remove_ttl,
    is_expired,
    purge_expired,
)


@pytest.fixture
def data():
    return {"API_KEY": "secret", "DB_PASS": "hunter2"}


def test_set_ttl_stores_expiry(data):
    result = set_ttl(data, "API_KEY", 60)
    assert TTL_META_KEY in result
    assert "API_KEY" in result[TTL_META_KEY]
    assert result[TTL_META_KEY]["API_KEY"] > time.time()


def test_set_ttl_raises_for_missing_key(data):
    with pytest.raises(TTLError, match="not found"):
        set_ttl(data, "NONEXISTENT", 60)


def test_set_ttl_raises_for_zero_seconds(data):
    with pytest.raises(TTLError, match="positive"):
        set_ttl(data, "API_KEY", 0)


def test_set_ttl_raises_for_negative_seconds(data):
    with pytest.raises(TTLError, match="positive"):
        set_ttl(data, "API_KEY", -5)


def test_get_ttl_returns_none_when_not_set(data):
    assert get_ttl(data, "API_KEY") is None


def test_get_ttl_returns_timestamp_after_set(data):
    set_ttl(data, "API_KEY", 30)
    ts = get_ttl(data, "API_KEY")
    assert isinstance(ts, float)
    assert ts > time.time()


def test_remove_ttl_clears_entry(data):
    set_ttl(data, "API_KEY", 60)
    remove_ttl(data, "API_KEY")
    assert get_ttl(data, "API_KEY") is None


def test_remove_ttl_removes_meta_key_when_empty(data):
    set_ttl(data, "API_KEY", 60)
    remove_ttl(data, "API_KEY")
    assert TTL_META_KEY not in data


def test_is_expired_false_for_future_ttl(data):
    set_ttl(data, "API_KEY", 3600)
    assert is_expired(data, "API_KEY") is False


def test_is_expired_true_for_past_ttl(data):
    meta = {"API_KEY": time.time() - 1}
    data[TTL_META_KEY] = meta
    assert is_expired(data, "API_KEY") is True


def test_is_expired_false_when_no_ttl(data):
    assert is_expired(data, "API_KEY") is False


def test_purge_expired_removes_stale_keys(data):
    data[TTL_META_KEY] = {"API_KEY": time.time() - 1}
    removed = purge_expired(data)
    assert "API_KEY" in removed
    assert "API_KEY" not in data


def test_purge_expired_keeps_valid_keys(data):
    set_ttl(data, "API_KEY", 3600)
    removed = purge_expired(data)
    assert removed == []
    assert "API_KEY" in data


def test_purge_expired_cleans_meta_when_all_gone(data):
    data[TTL_META_KEY] = {"API_KEY": time.time() - 1, "DB_PASS": time.time() - 1}
    purge_expired(data)
    assert TTL_META_KEY not in data
