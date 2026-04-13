"""Observe module: track read access to vault variables."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

OBSERVE_FILENAME = ".observe_log"


class ObserveError(Exception):
    """Raised when an observe operation fails."""


def _observe_path(vault_name: str, vault_dir: Path) -> Path:
    return vault_dir / f"{vault_name}{OBSERVE_FILENAME}"


def record_read(
    vault_name: str,
    key: str,
    actor: str = "unknown",
    *,
    vault_dir: Path,
) -> None:
    """Append a read-access event for *key* in *vault_name*."""
    path = _observe_path(vault_name, vault_dir)
    entry = {
        "ts": time.time(),
        "vault": vault_name,
        "key": key,
        "actor": actor,
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def read_observations(
    vault_name: str,
    *,
    vault_dir: Path,
    key: str | None = None,
) -> list[dict[str, Any]]:
    """Return all recorded read events, optionally filtered by *key*."""
    path = _observe_path(vault_name, vault_dir)
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ObserveError(f"Corrupt observation log: {exc}") from exc
            if key is None or entry.get("key") == key:
                events.append(entry)
    return events


def clear_observations(vault_name: str, *, vault_dir: Path) -> int:
    """Delete all observations for *vault_name*. Returns number of entries removed."""
    path = _observe_path(vault_name, vault_dir)
    if not path.exists():
        return 0
    count = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    path.unlink()
    return count
