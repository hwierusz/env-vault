"""Trend analysis for vault variables based on audit history."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from env_vault.audit import read_events


class TrendError(Exception):
    """Raised when trend analysis fails."""


@dataclass
class TrendEntry:
    key: str
    total_reads: int
    total_writes: int
    total_deletes: int
    last_action: Optional[str] = None
    last_timestamp: Optional[str] = None

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"TrendEntry(key={self.key!r}, reads={self.total_reads}, "
            f"writes={self.total_writes}, deletes={self.total_deletes})"
        )

    @property
    def activity_score(self) -> int:
        """Simple weighted activity score."""
        return self.total_reads + self.total_writes * 2 + self.total_deletes * 3


def trend_vault(
    vault_name: str,
    reader: Callable[[str], List[dict]] = read_events,
) -> List[TrendEntry]:
    """Analyse audit events and return per-key trend entries.

    Args:
        vault_name: Name of the vault whose audit log to inspect.
        reader: Callable that returns a list of audit event dicts.

    Returns:
        List of TrendEntry objects sorted by activity_score descending.

    Raises:
        TrendError: If the audit log cannot be read.
    """
    try:
        events = reader(vault_name)
    except Exception as exc:  # pragma: no cover
        raise TrendError(f"Failed to read audit events: {exc}") from exc

    buckets: Dict[str, dict] = {}

    for event in events:
        key = event.get("key")
        if not key:
            continue
        action = event.get("action", "")
        timestamp = event.get("timestamp")

        if key not in buckets:
            buckets[key] = {
                "reads": 0,
                "writes": 0,
                "deletes": 0,
                "last_action": None,
                "last_timestamp": None,
            }

        b = buckets[key]
        if action == "get":
            b["reads"] += 1
        elif action in ("set", "rotate"):
            b["writes"] += 1
        elif action == "delete":
            b["deletes"] += 1

        if timestamp and (b["last_timestamp"] is None or timestamp > b["last_timestamp"]):
            b["last_timestamp"] = timestamp
            b["last_action"] = action

    entries = [
        TrendEntry(
            key=k,
            total_reads=v["reads"],
            total_writes=v["writes"],
            total_deletes=v["deletes"],
            last_action=v["last_action"],
            last_timestamp=v["last_timestamp"],
        )
        for k, v in buckets.items()
    ]
    entries.sort(key=lambda e: e.activity_score, reverse=True)
    return entries
