"""Normalize environment variable keys and values to a canonical form."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class NormalizeError(Exception):
    """Raised when normalization cannot produce a valid result."""


@dataclass
class NormalizeResult:
    original_key: str
    normalized_key: str
    original_value: str
    normalized_value: str
    changes: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"NormalizeResult({self.original_key!r} -> {self.normalized_key!r}, "
            f"changes={self.changes})"
        )

    @property
    def was_changed(self) -> bool:
        return bool(self.changes)


def normalize_key(key: str) -> tuple[str, list[str]]:
    """Return (normalized_key, list_of_changes)."""
    changes: List[str] = []
    result = key

    upper = result.upper()
    if upper != result:
        changes.append("key uppercased")
        result = upper

    sanitized = re.sub(r"[^A-Z0-9_]", "_", result)
    if sanitized != result:
        changes.append("invalid characters replaced with underscore")
        result = sanitized

    if result and result[0].isdigit():
        result = "_" + result
        changes.append("leading digit prefixed with underscore")

    if not result:
        raise NormalizeError(f"Key {key!r} normalizes to an empty string")

    return result, changes


def normalize_value(value: str) -> tuple[str, list[str]]:
    """Return (normalized_value, list_of_changes)."""
    changes: List[str] = []
    result = value

    stripped = result.strip()
    if stripped != result:
        changes.append("leading/trailing whitespace stripped")
        result = stripped

    # Remove surrounding quotes if present
    for quote in ('"', "'"):
        if len(result) >= 2 and result[0] == quote and result[-1] == quote:
            result = result[1:-1]
            changes.append(f"surrounding {quote} quotes removed")
            break

    return result, changes


def normalize_vars(
    variables: Dict[str, str],
    *,
    skip_errors: bool = False,
) -> List[NormalizeResult]:
    """Normalize all keys and values in *variables*.

    Returns a list of :class:`NormalizeResult` objects, one per entry.
    Raises :class:`NormalizeError` unless *skip_errors* is True.
    """
    results: List[NormalizeResult] = []
    for key, value in variables.items():
        try:
            norm_key, key_changes = normalize_key(key)
        except NormalizeError:
            if skip_errors:
                continue
            raise
        norm_value, value_changes = normalize_value(value)
        results.append(
            NormalizeResult(
                original_key=key,
                normalized_key=norm_key,
                original_value=value,
                normalized_value=norm_value,
                changes=key_changes + value_changes,
            )
        )
    return results
