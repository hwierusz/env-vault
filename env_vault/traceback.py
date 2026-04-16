"""Traceback: record and replay the origin of variable changes."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


class TracebackError(Exception):
    pass


@dataclass
class TraceEntry:
    key: str
    value: str
    source: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    note: Optional[str] = None

    def __repr__(self) -> str:
        return f"TraceEntry(key={self.key!r}, source={self.source!r}, ts={self.timestamp!r})"

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "source": self.source,
            "timestamp": self.timestamp,
            "note": self.note,
        }


def _trace_path(vault_dir: str, vault_name: str) -> str:
    return os.path.join(vault_dir, f"{vault_name}.trace.jsonl")


def record_trace(
    vault_dir: str,
    vault_name: str,
    key: str,
    value: str,
    source: str,
    note: Optional[str] = None,
) -> TraceEntry:
    if not key:
        raise TracebackError("key must not be empty")
    if not source:
        raise TracebackError("source must not be empty")
    entry = TraceEntry(key=key, value=value, source=source, note=note)
    path = _trace_path(vault_dir, vault_name)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry.to_dict()) + "\n")
    return entry


def read_traces(
    vault_dir: str,
    vault_name: str,
    key: Optional[str] = None,
) -> List[TraceEntry]:
    path = _trace_path(vault_dir, vault_name)
    if not os.path.exists(path):
        return []
    entries: List[TraceEntry] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            entry = TraceEntry(
                key=data["key"],
                value=data["value"],
                source=data["source"],
                timestamp=data["timestamp"],
                note=data.get("note"),
            )
            if key is None or entry.key == key:
                entries.append(entry)
    return entries


def clear_traces(vault_dir: str, vault_name: str) -> int:
    path = _trace_path(vault_dir, vault_name)
    if not os.path.exists(path):
        return 0
    count = sum(1 for line in open(path, encoding="utf-8") if line.strip())
    os.remove(path)
    return count
