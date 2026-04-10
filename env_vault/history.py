"""Variable change history tracking for env-vault."""

import json
import os
from datetime import datetime, timezone
from typing import List, Optional

HISTORY_FILENAME = ".history.jsonl"


class HistoryError(Exception):
    pass


def _history_path(vault_name: str, vault_dir: str) -> str:
    return os.path.join(vault_dir, f"{vault_name}{HISTORY_FILENAME}")


def record_change(
    vault_name: str,
    key: str,
    action: str,
    vault_dir: str,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
) -> None:
    """Append a change record for a vault variable.

    action must be one of: 'set', 'delete'.
    """
    if action not in ("set", "delete"):
        raise HistoryError(f"Unknown action '{action}'; must be 'set' or 'delete'.")

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "vault": vault_name,
        "key": key,
        "action": action,
    }
    if old_value is not None:
        entry["old_value"] = old_value
    if new_value is not None:
        entry["new_value"] = new_value

    path = _history_path(vault_name, vault_dir)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def read_history(
    vault_name: str,
    vault_dir: str,
    key: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[dict]:
    """Return history entries, optionally filtered by key and capped at limit."""
    path = _history_path(vault_name, vault_dir)
    if not os.path.exists(path):
        return []

    entries = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))

    if key is not None:
        entries = [e for e in entries if e.get("key") == key]

    if limit is not None:
        entries = entries[-limit:]

    return entries


def clear_history(vault_name: str, vault_dir: str) -> int:
    """Delete all history for a vault. Returns number of records removed."""
    path = _history_path(vault_name, vault_dir)
    if not os.path.exists(path):
        return 0
    count = len(read_history(vault_name, vault_dir))
    os.remove(path)
    return count
