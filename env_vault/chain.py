"""Variable chaining: resolve a key through an ordered list of vaults,
returning the first vault that contains the key."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional


class ChainError(Exception):
    """Raised when chain resolution fails."""


@dataclass
class ChainResult:
    key: str
    value: str
    source: str  # vault name where the value was found

    def __repr__(self) -> str:  # pragma: no cover
        return f"ChainResult(key={self.key!r}, source={self.source!r})"


def resolve_chain(
    key: str,
    vault_names: List[str],
    loader: Callable[[str], Dict[str, str]],
    exists: Callable[[str], bool],
) -> ChainResult:
    """Search *vault_names* in order and return the first hit for *key*.

    Parameters
    ----------
    key:
        The variable name to look up.
    vault_names:
        Ordered list of vault identifiers to search.
    loader:
        Callable that accepts a vault name and returns its variables dict.
    exists:
        Callable that returns True when a vault exists.

    Raises
    ------
    ChainError
        If *vault_names* is empty, a vault does not exist, or *key* is not
        found in any vault.
    """
    if not vault_names:
        raise ChainError("vault_names must not be empty")

    for name in vault_names:
        if not exists(name):
            raise ChainError(f"vault not found: {name!r}")
        variables = loader(name)
        if key in variables:
            return ChainResult(key=key, value=variables[key], source=name)

    raise ChainError(
        f"key {key!r} not found in any of the vaults: {vault_names}"
    )


def chain_sources(
    vault_names: List[str],
    loader: Callable[[str], Dict[str, str]],
    exists: Callable[[str], bool],
) -> Dict[str, str]:
    """Return a merged dict of all variables, with earlier vaults taking
    precedence (first-wins semantics)."""
    if not vault_names:
        raise ChainError("vault_names must not be empty")

    merged: Dict[str, str] = {}
    for name in reversed(vault_names):
        if not exists(name):
            raise ChainError(f"vault not found: {name!r}")
        merged.update(loader(name))
    return merged
