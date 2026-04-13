"""Subscription module: track which users/services are subscribed to vault keys."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class SubscriptionError(Exception):
    """Raised when a subscription operation fails."""


@dataclass
class SubscriptionEntry:
    key: str
    subscriber: str
    channel: str = "default"
    tags: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"SubscriptionEntry(key={self.key!r}, subscriber={self.subscriber!r}, "
            f"channel={self.channel!r})"
        )


def _get_subscriptions(data: dict) -> Dict[str, List[dict]]:
    return data.setdefault("__subscriptions__", {})


def subscribe(
    vault_name: str,
    key: str,
    subscriber: str,
    channel: str = "default",
    tags: Optional[List[str]] = None,
    load_fn=None,
    save_fn=None,
) -> SubscriptionEntry:
    """Add a subscriber to a vault key."""
    data = load_fn(vault_name)
    if key not in data:
        raise SubscriptionError(f"Key {key!r} not found in vault {vault_name!r}")
    subs = _get_subscriptions(data)
    entries = subs.setdefault(key, [])
    for e in entries:
        if e["subscriber"] == subscriber and e["channel"] == channel:
            raise SubscriptionError(
                f"{subscriber!r} already subscribed to {key!r} on channel {channel!r}"
            )
    entry = {"subscriber": subscriber, "channel": channel, "tags": tags or []}
    entries.append(entry)
    save_fn(vault_name, data)
    return SubscriptionEntry(key=key, **entry)


def unsubscribe(
    vault_name: str, key: str, subscriber: str, channel: str = "default",
    load_fn=None, save_fn=None,
) -> bool:
    """Remove a subscriber from a vault key. Returns True if removed."""
    data = load_fn(vault_name)
    subs = _get_subscriptions(data)
    entries = subs.get(key, [])
    new_entries = [e for e in entries if not (e["subscriber"] == subscriber and e["channel"] == channel)]
    if len(new_entries) == len(entries):
        return False
    subs[key] = new_entries
    save_fn(vault_name, data)
    return True


def list_subscriptions(vault_name: str, key: str, load_fn=None) -> List[SubscriptionEntry]:
    """Return all subscriptions for a given key."""
    data = load_fn(vault_name)
    subs = _get_subscriptions(data)
    return [
        SubscriptionEntry(key=key, **e)
        for e in subs.get(key, [])
    ]


def list_all_subscriptions(vault_name: str, load_fn=None) -> Dict[str, List[SubscriptionEntry]]:
    """Return all subscriptions across all keys."""
    data = load_fn(vault_name)
    subs = _get_subscriptions(data)
    return {
        k: [SubscriptionEntry(key=k, **e) for e in entries]
        for k, entries in subs.items()
    }
