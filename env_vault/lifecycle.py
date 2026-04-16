"""Lifecycle management: track creation, modification, and archival of vault keys."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

LIFECYCLE_STATES = ("active", "deprecated", "archived")


class LifecycleError(Exception):
    pass


@dataclass
class LifecycleEntry:
    key: str
    state: str
    created_at: str
    updated_at: str
    note: Optional[str] = None

    def __repr__(self) -> str:
        return f"LifecycleEntry(key={self.key!r}, state={self.state!r})"

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "state": self.state,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "note": self.note,
        }


def _get_lifecycle(data: dict) -> dict:
    return data.setdefault("__lifecycle__", {})


def set_lifecycle(
    vault_name: str,
    key: str,
    state: str,
    note: Optional[str],
    load_fn: Callable,
    save_fn: Callable,
) -> LifecycleEntry:
    if state not in LIFECYCLE_STATES:
        raise LifecycleError(f"Invalid state {state!r}. Choose from {LIFECYCLE_STATES}.")
    data = load_fn(vault_name)
    if key not in data.get("vars", {}):
        raise LifecycleError(f"Key {key!r} not found in vault {vault_name!r}.")
    lc = _get_lifecycle(data)
    now = datetime.now(timezone.utc).isoformat()
    existing = lc.get(key, {})
    entry = LifecycleEntry(
        key=key,
        state=state,
        created_at=existing.get("created_at", now),
        updated_at=now,
        note=note,
    )
    lc[key] = entry.to_dict()
    save_fn(vault_name, data)
    return entry


def get_lifecycle(vault_name: str, key: str, load_fn: Callable) -> Optional[LifecycleEntry]:
    data = load_fn(vault_name)
    record = _get_lifecycle(data).get(key)
    if record is None:
        return None
    return LifecycleEntry(**record)


def list_lifecycle(vault_name: str, load_fn: Callable) -> List[LifecycleEntry]:
    data = load_fn(vault_name)
    return [LifecycleEntry(**v) for v in _get_lifecycle(data).values()]


def remove_lifecycle(vault_name: str, key: str, load_fn: Callable, save_fn: Callable) -> bool:
    data = load_fn(vault_name)
    lc = _get_lifecycle(data)
    if key not in lc:
        return False
    del lc[key]
    save_fn(vault_name, data)
    return True
