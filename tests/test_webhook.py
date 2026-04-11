"""Tests for env_vault.webhook."""

from __future__ import annotations

import pytest

from env_vault.webhook import (
    WebhookError,
    WebhookEntry,
    add_webhook,
    remove_webhook,
    list_webhooks,
    fire_event,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

URL_A = "https://example.com/hook"
URL_B = "https://other.io/notify"


def _make_load(data: dict):
    def _load(name, pw):
        return dict(data)
    return _load


def _make_save(store: dict):
    def _save(name, pw, d):
        store.update(d)
    return _save


@pytest.fixture()
def mock_vault(monkeypatch):
    """Patch vault_exists to always return True."""
    monkeypatch.setattr("env_vault.webhook.vault_exists", lambda _: True)


# ---------------------------------------------------------------------------
# add_webhook
# ---------------------------------------------------------------------------

def test_add_webhook_stores_entry(mock_vault):
    store: dict = {}
    add_webhook("myapp", "pw", URL_A,
                load_fn=_make_load({}), save_fn=_make_save(store))
    assert store["__webhooks__"][0]["url"] == URL_A


def test_add_webhook_with_events(mock_vault):
    store: dict = {}
    add_webhook("myapp", "pw", URL_A, ["set", "delete"],
                load_fn=_make_load({}), save_fn=_make_save(store))
    assert store["__webhooks__"][0]["events"] == ["set", "delete"]


def test_add_webhook_duplicate_raises(mock_vault):
    existing = {"__webhooks__": [{"url": URL_A, "events": []}]}
    with pytest.raises(WebhookError, match="already registered"):
        add_webhook("myapp", "pw", URL_A,
                    load_fn=_make_load(existing), save_fn=_make_save({}))


def test_add_webhook_missing_vault(monkeypatch):
    monkeypatch.setattr("env_vault.webhook.vault_exists", lambda _: False)
    with pytest.raises(WebhookError, match="does not exist"):
        add_webhook("ghost", "pw", URL_A)


# ---------------------------------------------------------------------------
# remove_webhook
# ---------------------------------------------------------------------------

def test_remove_webhook_deletes_entry(mock_vault):
    existing = {"__webhooks__": [{"url": URL_A, "events": []}]}
    store: dict = dict(existing)
    remove_webhook("myapp", "pw", URL_A,
                   load_fn=_make_load(existing), save_fn=_make_save(store))
    assert store["__webhooks__"] == []


def test_remove_webhook_unknown_raises(mock_vault):
    with pytest.raises(WebhookError, match="not found"):
        remove_webhook("myapp", "pw", URL_A,
                       load_fn=_make_load({}), save_fn=_make_save({}))


# ---------------------------------------------------------------------------
# list_webhooks
# ---------------------------------------------------------------------------

def test_list_webhooks_returns_entries(mock_vault):
    data = {"__webhooks__": [
        {"url": URL_A, "events": []},
        {"url": URL_B, "events": ["set"]},
    ]}
    hooks = list_webhooks("myapp", "pw", load_fn=_make_load(data))
    assert len(hooks) == 2
    assert isinstance(hooks[0], WebhookEntry)
    assert hooks[1].events == ["set"]


def test_list_webhooks_empty(mock_vault):
    hooks = list_webhooks("myapp", "pw", load_fn=_make_load({}))
    assert hooks == []


# ---------------------------------------------------------------------------
# fire_event
# ---------------------------------------------------------------------------

def test_fire_event_calls_matching_hooks(mock_vault):
    data = {"__webhooks__": [
        {"url": URL_A, "events": []},          # all events
        {"url": URL_B, "events": ["delete"]},  # only delete
    ]}
    posted: list[str] = []

    def _fake_post(url, body):
        posted.append(url)

    notified = fire_event("myapp", "pw", "set",
                          load_fn=_make_load(data), http_post=_fake_post)
    assert URL_A in notified
    assert URL_B not in notified


def test_fire_event_no_match_returns_empty(mock_vault):
    data = {"__webhooks__": [{"url": URL_A, "events": ["rotate"]}]}
    notified = fire_event("myapp", "pw", "set",
                          load_fn=_make_load(data), http_post=lambda u, b: None)
    assert notified == []
