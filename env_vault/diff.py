"""Diff two vaults or a vault against a dotenv file."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from env_vault.storage import load_vault, vault_exists


class DiffError(Exception):
    """Raised when a diff operation fails."""


@dataclass
class DiffEntry:
    key: str
    status: str          # 'added' | 'removed' | 'changed' | 'unchanged'
    left_value: Optional[str] = None
    right_value: Optional[str] = None

    def __repr__(self) -> str:  # pragma: no cover
        return f"DiffEntry(key={self.key!r}, status={self.status!r})"


def diff_vaults(
    left_name: str,
    left_password: str,
    right_name: str,
    right_password: str,
    *,
    show_unchanged: bool = False,
) -> List[DiffEntry]:
    """Compare two named vaults and return a list of DiffEntry objects."""
    if not vault_exists(left_name):
        raise DiffError(f"Vault '{left_name}' does not exist.")
    if not vault_exists(right_name):
        raise DiffError(f"Vault '{right_name}' does not exist.")

    left: Dict[str, str] = load_vault(left_name, left_password)
    right: Dict[str, str] = load_vault(right_name, right_password)

    return _compute_diff(left, right, show_unchanged=show_unchanged)


def diff_vault_against_dict(
    vault_name: str,
    password: str,
    other: Dict[str, str],
    *,
    show_unchanged: bool = False,
) -> List[DiffEntry]:
    """Compare a named vault against an in-memory dict (e.g. parsed dotenv)."""
    if not vault_exists(vault_name):
        raise DiffError(f"Vault '{vault_name}' does not exist.")

    vault: Dict[str, str] = load_vault(vault_name, password)
    return _compute_diff(vault, other, show_unchanged=show_unchanged)


def _compute_diff(
    left: Dict[str, str],
    right: Dict[str, str],
    *,
    show_unchanged: bool,
) -> List[DiffEntry]:
    entries: List[DiffEntry] = []
    all_keys = sorted(set(left) | set(right))

    for key in all_keys:
        in_left = key in left
        in_right = key in right

        if in_left and in_right:
            if left[key] == right[key]:
                if show_unchanged:
                    entries.append(DiffEntry(key, "unchanged", left[key], right[key]))
            else:
                entries.append(DiffEntry(key, "changed", left[key], right[key]))
        elif in_left:
            entries.append(DiffEntry(key, "removed", left[key], None))
        else:
            entries.append(DiffEntry(key, "added", None, right[key]))

    return entries
