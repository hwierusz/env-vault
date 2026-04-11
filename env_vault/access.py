"""Access control: restrict vault operations to allowed users/roles."""
from __future__ import annotations

import getpass
from typing import Dict, List, Optional


class AccessError(Exception):
    pass


_ACCESS_KEY = "__access_control__"


def _get_acl(data: dict) -> Dict[str, List[str]]:
    """Return the ACL dict: {username: [permission, ...]}"""
    return data.get(_ACCESS_KEY, {})


def grant_access(
    vault_name: str,
    username: str,
    permissions: List[str],
    load_fn,
    save_fn,
) -> None:
    """Grant *permissions* to *username* in the given vault."""
    valid = {"read", "write", "admin"}
    bad = set(permissions) - valid
    if bad:
        raise AccessError(f"Unknown permissions: {bad}. Valid: {valid}")
    data = load_fn(vault_name)
    acl: Dict[str, List[str]] = _get_acl(data)
    existing = set(acl.get(username, []))
    existing.update(permissions)
    acl[username] = sorted(existing)
    data[_ACCESS_KEY] = acl
    save_fn(vault_name, data)


def revoke_access(
    vault_name: str,
    username: str,
    permissions: Optional[List[str]],
    load_fn,
    save_fn,
) -> None:
    """Revoke specific (or all) permissions from *username*."""
    data = load_fn(vault_name)
    acl = _get_acl(data)
    if username not in acl:
        raise AccessError(f"User '{username}' has no access entry.")
    if permissions is None:
        del acl[username]
    else:
        remaining = set(acl[username]) - set(permissions)
        if remaining:
            acl[username] = sorted(remaining)
        else:
            del acl[username]
    data[_ACCESS_KEY] = acl
    save_fn(vault_name, data)


def list_access(vault_name: str, load_fn) -> Dict[str, List[str]]:
    """Return the full ACL for the vault."""
    data = load_fn(vault_name)
    return dict(_get_acl(data))


def check_access(vault_name: str, permission: str, load_fn) -> bool:
    """Return True if the current OS user holds *permission*."""
    data = load_fn(vault_name)
    acl = _get_acl(data)
    if not acl:
        return True  # no ACL configured — open access
    username = getpass.getuser()
    user_perms = set(acl.get(username, []))
    return permission in user_perms or "admin" in user_perms
