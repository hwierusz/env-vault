"""Tests for env_vault.subscription."""
import pytest
from env_vault.subscription import (
    SubscriptionError,
    SubscriptionEntry,
    subscribe,
    unsubscribe,
    list_subscriptions,
    list_all_subscriptions,
)


def _make_load(data):
    def _load(name):
        return data
    return _load


def _make_save(store):
    def _save(name, d):
        store.clear()
        store.update(d)
    return _save


@pytest.fixture()
def base_data():
    return {"API_KEY": "secret", "DB_URL": "postgres://localhost/db"}


def test_subscribe_stores_entry(base_data):
    store = dict(base_data)
    entry = subscribe("v", "API_KEY", "alice", load_fn=_make_load(store), save_fn=_make_save(store))
    assert isinstance(entry, SubscriptionEntry)
    assert entry.key == "API_KEY"
    assert entry.subscriber == "alice"
    assert entry.channel == "default"


def test_subscribe_custom_channel(base_data):
    store = dict(base_data)
    entry = subscribe("v", "API_KEY", "bob", channel="alerts", load_fn=_make_load(store), save_fn=_make_save(store))
    assert entry.channel == "alerts"


def test_subscribe_with_tags(base_data):
    store = dict(base_data)
    entry = subscribe("v", "API_KEY", "carol", tags=["prod", "critical"], load_fn=_make_load(store), save_fn=_make_save(store))
    assert "prod" in entry.tags


def test_subscribe_missing_key_raises(base_data):
    store = dict(base_data)
    with pytest.raises(SubscriptionError, match="not found"):
        subscribe("v", "MISSING", "alice", load_fn=_make_load(store), save_fn=_make_save(store))


def test_subscribe_duplicate_raises(base_data):
    store = dict(base_data)
    subscribe("v", "API_KEY", "alice", load_fn=_make_load(store), save_fn=_make_save(store))
    with pytest.raises(SubscriptionError, match="already subscribed"):
        subscribe("v", "API_KEY", "alice", load_fn=_make_load(store), save_fn=_make_save(store))


def test_unsubscribe_returns_true(base_data):
    store = dict(base_data)
    subscribe("v", "API_KEY", "alice", load_fn=_make_load(store), save_fn=_make_save(store))
    removed = unsubscribe("v", "API_KEY", "alice", load_fn=_make_load(store), save_fn=_make_save(store))
    assert removed is True


def test_unsubscribe_nonexistent_returns_false(base_data):
    store = dict(base_data)
    removed = unsubscribe("v", "API_KEY", "nobody", load_fn=_make_load(store), save_fn=_make_save(store))
    assert removed is False


def test_list_subscriptions_returns_entries(base_data):
    store = dict(base_data)
    subscribe("v", "API_KEY", "alice", load_fn=_make_load(store), save_fn=_make_save(store))
    subscribe("v", "API_KEY", "bob", channel="alerts", load_fn=_make_load(store), save_fn=_make_save(store))
    entries = list_subscriptions("v", "API_KEY", load_fn=_make_load(store))
    assert len(entries) == 2
    subscribers = {e.subscriber for e in entries}
    assert subscribers == {"alice", "bob"}


def test_list_subscriptions_empty_key(base_data):
    store = dict(base_data)
    entries = list_subscriptions("v", "API_KEY", load_fn=_make_load(store))
    assert entries == []


def test_list_all_subscriptions(base_data):
    store = dict(base_data)
    subscribe("v", "API_KEY", "alice", load_fn=_make_load(store), save_fn=_make_save(store))
    subscribe("v", "DB_URL", "bob", load_fn=_make_load(store), save_fn=_make_save(store))
    mapping = list_all_subscriptions("v", load_fn=_make_load(store))
    assert "API_KEY" in mapping
    assert "DB_URL" in mapping


def test_repr_subscription_entry():
    e = SubscriptionEntry(key="K", subscriber="s", channel="c")
    assert "K" in repr(e)
    assert "s" in repr(e)
