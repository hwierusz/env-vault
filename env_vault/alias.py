"""Alias support: map short names to vault variable keys."""

from __future__ import annotations

from typing import Dict, Optional

from env_vault.storage import load_vault, save_vault

_ALIAS_NS = "__aliases__"


class AliasError(Exception):
    pass


def _get_aliases(data: dict) -> Dict[str, str]:
    return data.get(_ALIAS_NS, {})


def add_alias(
    vault_name: str,
    password: str,
    alias: str,
    target_key: str,
    load_fn=load_vault,
    save_fn=save_vault,
) -> None:
    """Register *alias* as a shorthand for *target_key*."""
    if not alias.isidentifier():
        raise AliasError(f"Invalid alias name: {alias!r}")
    data = load_fn(vault_name, password)
    if target_key not in data:
        raise AliasError(f"Target key {target_key!r} does not exist in vault")
    aliases = _get_aliases(data)
    aliases[alias] = target_key
    data[_ALIAS_NS] = aliases
    save_fn(vault_name, password, data)


def remove_alias(
    vault_name: str,
    password: str,
    alias: str,
    load_fn=load_vault,
    save_fn=save_vault,
) -> None:
    """Remove an existing alias."""
    data = load_fn(vault_name, password)
    aliases = _get_aliases(data)
    if alias not in aliases:
        raise AliasError(f"Alias {alias!r} not found")
    del aliases[alias]
    data[_ALIAS_NS] = aliases
    save_fn(vault_name, password, data)


def resolve_alias(
    vault_name: str,
    password: str,
    alias: str,
    load_fn=load_vault,
) -> Optional[str]:
    """Return the key that *alias* points to, or None if not found."""
    data = load_fn(vault_name, password)
    return _get_aliases(data).get(alias)


def list_aliases(
    vault_name: str,
    password: str,
    load_fn=load_vault,
) -> Dict[str, str]:
    """Return all alias -> key mappings for the vault."""
    data = load_fn(vault_name, password)
    return dict(_get_aliases(data))
