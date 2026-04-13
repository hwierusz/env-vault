"""Delegation: allow one key to act as a proxy for another key's value."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

VaultData = Dict
Loader = Callable[[str], VaultData]
Saver = Callable[[str, VaultData], None]

_SECTION = "__delegates__"


class DelegateError(Exception):
    """Raised on delegation-related errors."""


@dataclass
class DelegateEntry:
    key: str
    target: str
    description: str = ""

    def __repr__(self) -> str:  # pragma: no cover
        return f"DelegateEntry(key={self.key!r}, target={self.target!r})"


def _get_delegates(data: VaultData) -> Dict[str, Dict]:
    return data.setdefault(_SECTION, {})


def add_delegate(
    vault_name: str,
    key: str,
    target: str,
    description: str = "",
    *,
    load: Loader,
    save: Saver,
) -> None:
    """Register *key* as a delegate for *target*."""
    data = load(vault_name)
    vars_ = data.get("vars", {})
    if key not in vars_:
        raise DelegateError(f"Key {key!r} not found in vault {vault_name!r}")
    if target not in vars_:
        raise DelegateError(f"Target key {target!r} not found in vault {vault_name!r}")
    if key == target:
        raise DelegateError("A key cannot delegate to itself")
    delegates = _get_delegates(data)
    delegates[key] = {"target": target, "description": description}
    save(vault_name, data)


def remove_delegate(vault_name: str, key: str, *, load: Loader, save: Saver) -> None:
    """Remove the delegation for *key*."""
    data = load(vault_name)
    delegates = _get_delegates(data)
    if key not in delegates:
        raise DelegateError(f"No delegation found for key {key!r}")
    del delegates[key]
    save(vault_name, data)


def resolve_delegate(
    vault_name: str, key: str, *, load: Loader
) -> Optional[str]:
    """Return the resolved value following the delegation chain.

    Raises *DelegateError* if a cycle is detected.
    """
    data = load(vault_name)
    vars_ = data.get("vars", {})
    delegates = _get_delegates(data)
    visited: List[str] = []
    current = key
    while current in delegates:
        if current in visited:
            raise DelegateError(f"Delegation cycle detected: {' -> '.join(visited + [current])}")
        visited.append(current)
        current = delegates[current]["target"]
    return vars_.get(current)


def list_delegates(vault_name: str, *, load: Loader) -> List[DelegateEntry]:
    """Return all registered delegations for *vault_name*."""
    data = load(vault_name)
    delegates = _get_delegates(data)
    return [
        DelegateEntry(key=k, target=v["target"], description=v.get("description", ""))
        for k, v in delegates.items()
    ]
