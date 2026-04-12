"""Immutable key management — prevent accidental modification or deletion of critical vars."""

from __future__ import annotations

from typing import Any

_IMMUTABLE_SECTION = "__immutable__"


class ImmutableError(Exception):
    """Raised when an immutable constraint is violated."""


def _get_immutable(data: dict) -> dict:
    return data.setdefault(_IMMUTABLE_SECTION, {})


def lock_key(vault_name: str, key: str, reason: str = "",
             load_fn=None, save_fn=None) -> None:
    """Mark *key* as immutable inside *vault_name*."""
    from env_vault.storage import load_vault, save_vault
    load_fn = load_fn or load_vault
    save_fn = save_fn or save_vault

    data = load_fn(vault_name)
    if key not in data.get("vars", {}):
        raise ImmutableError(f"Key '{key}' does not exist in vault '{vault_name}'.")

    immutable = _get_immutable(data)
    immutable[key] = {"reason": reason}
    save_fn(vault_name, data)


def unlock_key(vault_name: str, key: str,
               load_fn=None, save_fn=None) -> None:
    """Remove the immutable lock from *key*."""
    from env_vault.storage import load_vault, save_vault
    load_fn = load_fn or load_vault
    save_fn = save_fn or save_vault

    data = load_fn(vault_name)
    immutable = _get_immutable(data)
    if key not in immutable:
        raise ImmutableError(f"Key '{key}' is not locked in vault '{vault_name}'.")

    del immutable[key]
    save_fn(vault_name, data)


def is_locked(vault_name: str, key: str, load_fn=None) -> bool:
    """Return True if *key* is marked immutable."""
    from env_vault.storage import load_vault
    load_fn = load_fn or load_vault
    data = load_fn(vault_name)
    return key in _get_immutable(data)


def list_locked(vault_name: str, load_fn=None) -> dict[str, Any]:
    """Return a mapping of locked keys to their metadata."""
    from env_vault.storage import load_vault
    load_fn = load_fn or load_vault
    data = load_fn(vault_name)
    return dict(_get_immutable(data))


def assert_mutable(vault_name: str, key: str, load_fn=None) -> None:
    """Raise ImmutableError if *key* is locked."""
    if is_locked(vault_name, key, load_fn=load_fn):
        raise ImmutableError(
            f"Key '{key}' is immutable and cannot be modified or deleted."
        )
