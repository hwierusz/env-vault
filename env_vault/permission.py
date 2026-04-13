"""Permission system for env-vault: assign read/write/admin permissions to users per vault."""

from __future__ import annotations

from typing import Callable, Dict, List, Optional

VALID_PERMISSIONS = {"read", "write", "admin"}


class PermissionError(Exception):
    """Raised when a permission operation fails."""


def _get_permissions(data: dict) -> dict:
    return data.setdefault("__permissions__", {})


def grant_permission(
    vault_name: str,
    user: str,
    permission: str,
    load: Callable,
    save: Callable,
) -> None:
    """Grant *permission* to *user* on *vault_name*."""
    if permission not in VALID_PERMISSIONS:
        raise PermissionError(
            f"Invalid permission '{permission}'. Must be one of: {sorted(VALID_PERMISSIONS)}"
        )
    if not user or not user.strip():
        raise PermissionError("User must be a non-empty string.")
    data = load(vault_name)
    perms = _get_permissions(data)
    user_perms: List[str] = perms.setdefault(user, [])
    if permission not in user_perms:
        user_perms.append(permission)
    save(vault_name, data)


def revoke_permission(
    vault_name: str,
    user: str,
    permission: str,
    load: Callable,
    save: Callable,
) -> None:
    """Revoke *permission* from *user* on *vault_name*."""
    data = load(vault_name)
    perms = _get_permissions(data)
    user_perms: List[str] = perms.get(user, [])
    if permission not in user_perms:
        raise PermissionError(
            f"User '{user}' does not have permission '{permission}'."
        )
    user_perms.remove(permission)
    if not user_perms:
        del perms[user]
    save(vault_name, data)


def list_permissions(
    vault_name: str,
    user: Optional[str],
    load: Callable,
) -> Dict[str, List[str]]:
    """Return all permissions or those for a specific *user*."""
    data = load(vault_name)
    perms = _get_permissions(data)
    if user is not None:
        return {user: list(perms.get(user, []))}
    return {u: list(p) for u, p in perms.items()}


def check_permission(
    vault_name: str,
    user: str,
    permission: str,
    load: Callable,
) -> bool:
    """Return True if *user* holds *permission* on *vault_name*."""
    data = load(vault_name)
    perms = _get_permissions(data)
    return permission in perms.get(user, [])
