"""Watch a vault for changes and trigger callbacks."""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from env_vault.storage import load_vault, vault_exists


class WatchError(Exception):
    pass


@dataclass
class WatchEvent:
    vault_name: str
    added: Dict[str, str] = field(default_factory=dict)
    removed: List[str] = field(default_factory=list)
    changed: Dict[str, str] = field(default_factory=dict)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"WatchEvent(vault={self.vault_name!r}, "
            f"added={list(self.added)}, "
            f"removed={self.removed}, "
            f"changed={list(self.changed)})"
        )

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)


def _diff_snapshots(
    old: Dict[str, str], new: Dict[str, str]
) -> WatchEvent:
    """Compute the difference between two vault snapshots."""
    event = WatchEvent(vault_name="")
    for key, value in new.items():
        if key not in old:
            event.added[key] = value
        elif old[key] != value:
            event.changed[key] = value
    for key in old:
        if key not in new:
            event.removed.append(key)
    return event


def watch_vault(
    vault_name: str,
    password: str,
    callback: Callable[[WatchEvent], None],
    interval: float = 2.0,
    stop_event: Optional[threading.Event] = None,
    load_fn=None,
) -> None:
    """Poll a vault for changes and invoke *callback* on each change.

    Blocks until *stop_event* is set (or forever if not provided).
    """
    if not vault_exists(vault_name):
        raise WatchError(f"Vault '{vault_name}' does not exist.")

    _load = load_fn or (lambda name, pw: load_vault(name, pw))

    try:
        previous = _load(vault_name, password)
    except Exception as exc:
        raise WatchError(f"Cannot read vault: {exc}") from exc

    stop = stop_event or threading.Event()

    while not stop.is_set():
        time.sleep(interval)
        try:
            current = _load(vault_name, password)
        except Exception:
            continue

        event = _diff_snapshots(previous, current)
        event.vault_name = vault_name
        if event.has_changes:
            callback(event)
        previous = current
