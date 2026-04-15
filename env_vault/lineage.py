"""Lineage tracking: record and query the origin/derivation history of vault keys."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


class LineageError(Exception):
    """Raised when a lineage operation fails."""


@dataclass
class LineageEntry:
    key: str
    source: str  # vault name or external label
    derived_from: Optional[str] = None  # parent key, if any
    note: Optional[str] = None

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"LineageEntry(key={self.key!r}, source={self.source!r}, "
            f"derived_from={self.derived_from!r})"
        )

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "source": self.source,
            "derived_from": self.derived_from,
            "note": self.note,
        }


def _get_lineage(data: dict) -> dict:
    return data.setdefault("__lineage__", {})


def record_lineage(
    vault_name: str,
    key: str,
    source: str,
    derived_from: Optional[str] = None,
    note: Optional[str] = None,
    *,
    load: Callable[[str], dict],
    save: Callable[[str, dict], None],
) -> LineageEntry:
    """Attach lineage metadata to *key* in *vault_name*."""
    data = load(vault_name)
    if key not in data.get("vars", {}) and key not in data:
        # Accept keys stored at top-level or under 'vars'
        vars_section = data.get("vars", data)
        if key not in vars_section:
            raise LineageError(f"Key {key!r} not found in vault {vault_name!r}")
    entry = LineageEntry(key=key, source=source, derived_from=derived_from, note=note)
    _get_lineage(data)[key] = entry.to_dict()
    save(vault_name, data)
    return entry


def get_lineage(
    vault_name: str,
    key: str,
    *,
    load: Callable[[str], dict],
) -> Optional[LineageEntry]:
    """Return the lineage entry for *key*, or None if not recorded."""
    data = load(vault_name)
    raw = _get_lineage(data).get(key)
    if raw is None:
        return None
    return LineageEntry(**raw)


def list_lineage(
    vault_name: str,
    *,
    load: Callable[[str], dict],
) -> List[LineageEntry]:
    """Return all lineage entries for *vault_name*."""
    data = load(vault_name)
    return [LineageEntry(**v) for v in _get_lineage(data).values()]


def remove_lineage(
    vault_name: str,
    key: str,
    *,
    load: Callable[[str], dict],
    save: Callable[[str, dict], None],
) -> bool:
    """Remove lineage metadata for *key*. Returns True if it existed."""
    data = load(vault_name)
    lineage = _get_lineage(data)
    if key not in lineage:
        return False
    del lineage[key]
    save(vault_name, data)
    return True
