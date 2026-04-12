"""Group management for env-vault: assign variables to named groups."""

from __future__ import annotations

from typing import Dict, List, Optional


class GroupError(Exception):
    """Raised when a group operation fails."""


_GROUPS_KEY = "__groups__"


def _get_groups(data: dict) -> Dict[str, List[str]]:
    return data.get(_GROUPS_KEY, {})


def add_to_group(data: dict, group: str, key: str) -> dict:
    """Add *key* to *group*. Raises GroupError if *key* is not in the vault."""
    if key not in data:
        raise GroupError(f"Key '{key}' does not exist in the vault.")
    if not group:
        raise GroupError("Group name must not be empty.")
    groups = _get_groups(data)
    members = groups.get(group, [])
    if key not in members:
        members.append(key)
    groups[group] = members
    data[_GROUPS_KEY] = groups
    return data


def remove_from_group(data: dict, group: str, key: str) -> dict:
    """Remove *key* from *group*. Raises GroupError if group or key not found."""
    groups = _get_groups(data)
    if group not in groups:
        raise GroupError(f"Group '{group}' does not exist.")
    members = groups[group]
    if key not in members:
        raise GroupError(f"Key '{key}' is not in group '{group}'.")
    members.remove(key)
    if not members:
        del groups[group]
    else:
        groups[group] = members
    data[_GROUPS_KEY] = groups
    return data


def list_groups(data: dict) -> List[str]:
    """Return sorted list of group names."""
    return sorted(_get_groups(data).keys())


def get_group_members(data: dict, group: str) -> List[str]:
    """Return members of *group*. Raises GroupError if group not found."""
    groups = _get_groups(data)
    if group not in groups:
        raise GroupError(f"Group '{group}' does not exist.")
    return list(groups[group])


def get_vars_for_group(data: dict, group: str) -> Dict[str, str]:
    """Return {key: value} dict for all members of *group* present in vault."""
    members = get_group_members(data, group)
    return {k: data[k] for k in members if k in data}


def delete_group(data: dict, group: str) -> dict:
    """Delete an entire group. Raises GroupError if group not found."""
    groups = _get_groups(data)
    if group not in groups:
        raise GroupError(f"Group '{group}' does not exist.")
    del groups[group]
    data[_GROUPS_KEY] = groups
    return data
