"""Audit log for tracking vault operations."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


def _audit_path(vault_name: str, vault_dir: Optional[str] = None) -> Path:
    """Return path to the audit log file for a given vault."""
    base = Path(vault_dir) if vault_dir else Path.home() / ".env_vault"
    return base / f"{vault_name}.audit.jsonl"


def record_event(
    vault_name: str,
    action: str,
    key: Optional[str] = None,
    vault_dir: Optional[str] = None,
) -> None:
    """Append an audit event to the vault's audit log."""
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "vault": vault_name,
        "action": action,
    }
    if key is not None:
        event["key"] = key

    audit_file = _audit_path(vault_name, vault_dir)
    audit_file.parent.mkdir(parents=True, exist_ok=True)

    with open(audit_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def read_events(
    vault_name: str,
    vault_dir: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[dict]:
    """Read audit events for a vault, newest first."""
    audit_file = _audit_path(vault_name, vault_dir)
    if not audit_file.exists():
        return []

    with open(audit_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    events = [json.loads(line) for line in lines]
    events.reverse()

    if limit is not None:
        return events[:limit]
    return events


def clear_events(vault_name: str, vault_dir: Optional[str] = None) -> None:
    """Remove the audit log for a vault."""
    audit_file = _audit_path(vault_name, vault_dir)
    if audit_file.exists():
        audit_file.unlink()
