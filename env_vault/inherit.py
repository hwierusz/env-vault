"""Vault inheritance: resolve variables by walking a parent chain."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


class InheritError(Exception):
    """Raised when inheritance resolution fails."""


@dataclass
class InheritResult:
    key: str
    value: str
    source_vault: str
    depth: int

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"InheritResult(key={self.key!r}, source={self.source_vault!r},"
            f" depth={self.depth})"
        )


def resolve_inherited(
    key: str,
    vaults: List[str],
    load_fn: Callable[[str, str], Dict[str, str]],
    exists_fn: Callable[[str], bool],
    password: str,
) -> InheritResult:
    """Walk *vaults* in order (child first) and return the first vault
    that defines *key*.

    Args:
        key: Variable name to look up.
        vaults: Ordered list of vault names, child at index 0.
        load_fn: Callable(vault_name, password) -> dict of vars.
        exists_fn: Callable(vault_name) -> bool.
        password: Decryption password shared across all vaults.

    Returns:
        :class:`InheritResult` describing where the value was found.

    Raises:
        InheritError: If *key* is not found in any vault or a vault is missing.
    """
    if not vaults:
        raise InheritError("No vaults provided for inheritance resolution.")

    for depth, vault_name in enumerate(vaults):
        if not exists_fn(vault_name):
            raise InheritError(f"Vault not found: {vault_name!r}")
        data = load_fn(vault_name, password)
        if key in data:
            return InheritResult(
                key=key,
                value=data[key],
                source_vault=vault_name,
                depth=depth,
            )

    raise InheritError(
        f"Key {key!r} not found in any of the provided vaults: {vaults}"
    )


def inherit_all(
    vaults: List[str],
    load_fn: Callable[[str, str], Dict[str, str]],
    exists_fn: Callable[[str], bool],
    password: str,
) -> Dict[str, InheritResult]:
    """Merge variables from all *vaults*, child entries taking precedence.

    Variables defined in earlier vaults (lower depth) shadow those in
    later vaults, mirroring how environment variable inheritance works.
    """
    if not vaults:
        raise InheritError("No vaults provided for inheritance resolution.")

    merged: Dict[str, InheritResult] = {}
    for depth, vault_name in reversed(list(enumerate(vaults))):
        if not exists_fn(vault_name):
            raise InheritError(f"Vault not found: {vault_name!r}")
        data = load_fn(vault_name, password)
        for k, v in data.items():
            merged[k] = InheritResult(
                key=k, value=v, source_vault=vault_name, depth=depth
            )
    return merged
