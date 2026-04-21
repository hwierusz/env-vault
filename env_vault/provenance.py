"""Provenance tracking: record and query the origin of vault variables."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from env_vault.storage import _vault_path


class ProvenanceError(Exception):
    """Raised when a provenance operation fails."""


@dataclass
class ProvenanceEntry:
    key: str
    source: str
    author: str
    timestamp: float = field(default_factory=time.time)
    note: str = ""

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ProvenanceEntry(key={self.key!r}, source={self.source!r}, "
            f"author={self.author!r})"
        )

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "source": self.source,
            "author": self.author,
            "timestamp": self.timestamp,
            "note": self.note,
        }


def _provenance_path(vault_name: str) -> Path:
    base = _vault_path(vault_name).parent
    return base / f"{vault_name}.provenance.jsonl"


def record_provenance(
    vault_name: str,
    key: str,
    source: str,
    author: str,
    note: str = "",
    vars_dict: Optional[dict] = None,
) -> ProvenanceEntry:
    """Record the origin of *key* in *vault_name*."""
    if not key:
        raise ProvenanceError("key must not be empty")
    if not source:
        raise ProvenanceError("source must not be empty")
    if not author:
        raise ProvenanceError("author must not be empty")
    if vars_dict is not None and key not in vars_dict:
        raise ProvenanceError(f"key {key!r} does not exist in vault")

    entry = ProvenanceEntry(key=key, source=source, author=author, note=note)
    path = _provenance_path(vault_name)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry.to_dict()) + "\n")
    return entry


def read_provenance(vault_name: str, key: Optional[str] = None) -> list[ProvenanceEntry]:
    """Return provenance entries, optionally filtered by *key*."""
    path = _provenance_path(vault_name)
    if not path.exists():
        return []
    entries: list[ProvenanceEntry] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            entry = ProvenanceEntry(**data)
            if key is None or entry.key == key:
                entries.append(entry)
    return entries


def clear_provenance(vault_name: str) -> None:
    """Delete all provenance records for *vault_name*."""
    path = _provenance_path(vault_name)
    if path.exists():
        path.unlink()
