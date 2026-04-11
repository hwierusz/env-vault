"""Reminder/expiry warnings for environment variables nearing their TTL deadline."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from env_vault.ttl import get_ttl, is_expired


class RemindError(Exception):
    """Raised when a reminder operation fails."""


@dataclass
class ReminderEntry:
    key: str
    seconds_remaining: float
    expired: bool

    def __repr__(self) -> str:  # pragma: no cover
        state = "EXPIRED" if self.expired else f"{int(self.seconds_remaining)}s remaining"
        return f"ReminderEntry(key={self.key!r}, {state})"


def check_reminders(
    vault_name: str,
    data: Dict,
    threshold_seconds: int = 86400,
    *,
    load_fn=None,
) -> List[ReminderEntry]:
    """Return variables whose TTL will expire within *threshold_seconds*.

    Args:
        vault_name: Name of the vault (passed to TTL helpers).
        data: Decrypted vault variable dict.
        threshold_seconds: Warn when TTL is below this value (default 24 h).
        load_fn: Optional override for storage.load_vault (testing).

    Returns:
        List of :class:`ReminderEntry` objects, sorted by seconds_remaining.
    """
    if threshold_seconds <= 0:
        raise RemindError("threshold_seconds must be a positive integer")

    now = time.time()
    entries: List[ReminderEntry] = []

    for key in data:
        expiry = get_ttl(vault_name, key, load_fn=load_fn)
        if expiry is None:
            continue
        seconds_remaining = expiry - now
        expired = seconds_remaining <= 0
        if expired or seconds_remaining <= threshold_seconds:
            entries.append(
                ReminderEntry(
                    key=key,
                    seconds_remaining=max(seconds_remaining, 0.0),
                    expired=expired,
                )
            )

    entries.sort(key=lambda e: e.seconds_remaining)
    return entries
