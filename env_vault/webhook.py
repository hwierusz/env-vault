"""Webhook notifications for vault events."""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional

from env_vault.storage import load_vault, save_vault, vault_exists

_WEBHOOK_KEY = "__webhooks__"


class WebhookError(Exception):
    pass


@dataclass
class WebhookEntry:
    url: str
    events: list[str] = field(default_factory=list)  # empty = all events

    def __repr__(self) -> str:  # pragma: no cover
        return f"WebhookEntry(url={self.url!r}, events={self.events!r})"


def _get_webhooks(data: dict) -> list[dict]:
    return data.get(_WEBHOOK_KEY, [])


def add_webhook(
    vault_name: str,
    password: str,
    url: str,
    events: Optional[list[str]] = None,
    *,
    load_fn=None,
    save_fn=None,
) -> None:
    """Register a webhook URL for a vault."""
    _load = load_fn or (lambda n, p: load_vault(n, p))
    _save = save_fn or (lambda n, p, d: save_vault(n, p, d))

    if not vault_exists(vault_name):
        raise WebhookError(f"Vault '{vault_name}' does not exist.")

    data = _load(vault_name, password)
    hooks = _get_webhooks(data)

    for h in hooks:
        if h["url"] == url:
            raise WebhookError(f"Webhook '{url}' is already registered.")

    hooks.append({"url": url, "events": events or []})
    data[_WEBHOOK_KEY] = hooks
    _save(vault_name, password, data)


def remove_webhook(
    vault_name: str,
    password: str,
    url: str,
    *,
    load_fn=None,
    save_fn=None,
) -> None:
    """Unregister a webhook URL from a vault."""
    _load = load_fn or (lambda n, p: load_vault(n, p))
    _save = save_fn or (lambda n, p, d: save_vault(n, p, d))

    if not vault_exists(vault_name):
        raise WebhookError(f"Vault '{vault_name}' does not exist.")

    data = _load(vault_name, password)
    hooks = _get_webhooks(data)
    new_hooks = [h for h in hooks if h["url"] != url]

    if len(new_hooks) == len(hooks):
        raise WebhookError(f"Webhook '{url}' not found.")

    data[_WEBHOOK_KEY] = new_hooks
    _save(vault_name, password, data)


def list_webhooks(
    vault_name: str,
    password: str,
    *,
    load_fn=None,
) -> list[WebhookEntry]:
    """Return all registered webhooks for a vault."""
    _load = load_fn or (lambda n, p: load_vault(n, p))

    if not vault_exists(vault_name):
        raise WebhookError(f"Vault '{vault_name}' does not exist.")

    data = _load(vault_name, password)
    return [WebhookEntry(url=h["url"], events=h["events"]) for h in _get_webhooks(data)]


def fire_event(
    vault_name: str,
    password: str,
    event: str,
    payload: Optional[dict] = None,
    *,
    load_fn=None,
    http_post=None,
) -> list[str]:
    """Send event to all matching webhooks. Returns list of URLs notified."""
    _load = load_fn or (lambda n, p: load_vault(n, p))
    _post = http_post or _default_post

    if not vault_exists(vault_name):
        raise WebhookError(f"Vault '{vault_name}' does not exist.")

    data = _load(vault_name, password)
    hooks = _get_webhooks(data)
    notified: list[str] = []

    body = json.dumps({
        "vault": vault_name,
        "event": event,
        "payload": payload or {},
    }).encode()

    for h in hooks:
        if not h["events"] or event in h["events"]:
            _post(h["url"], body)
            notified.append(h["url"])

    return notified


def _default_post(url: str, body: bytes) -> None:  # pragma: no cover
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5):
            pass
    except urllib.error.URLError as exc:
        raise WebhookError(f"Failed to POST to '{url}': {exc}") from exc
