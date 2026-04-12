"""Priority ordering for environment variables.

Allows assigning numeric priority levels to keys so that cascade
resolution and merge operations can respect precedence.
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

PRIORITY_SECTION = "__priorities__"


class PriorityError(Exception):
    """Raised when a priority operation fails."""


def _get_priorities(data: dict) -> dict:
    return data.setdefault(PRIORITY_SECTION, {})


def set_priority(
    vault_name: str,
    key: str,
    level: int,
    load: Callable,
    save: Callable,
) -> None:
    """Assign a numeric priority level to *key*.

    Higher numbers mean higher priority.  *level* must be >= 0.
    """
    if level < 0:
        raise PriorityError("Priority level must be >= 0")
    data = load(vault_name)
    if key not in data:
        raise PriorityError(f"Key '{key}' not found in vault '{vault_name}'")
    _get_priorities(data)[key] = level
    save(vault_name, data)


def get_priority(
    vault_name: str,
    key: str,
    load: Callable,
    default: int = 0,
) -> int:
    """Return the priority level for *key*, or *default* if not set."""
    data = load(vault_name)
    return _get_priorities(data).get(key, default)


def remove_priority(
    vault_name: str,
    key: str,
    load: Callable,
    save: Callable,
) -> None:
    """Remove the priority entry for *key*."""
    data = load(vault_name)
    priorities = _get_priorities(data)
    if key not in priorities:
        raise PriorityError(f"No priority set for key '{key}'")
    del priorities[key]
    save(vault_name, data)


def list_priorities(
    vault_name: str,
    load: Callable,
) -> List[Tuple[str, int]]:
    """Return all (key, level) pairs sorted by level descending."""
    data = load(vault_name)
    items = list(_get_priorities(data).items())
    return sorted(items, key=lambda x: x[1], reverse=True)


def sorted_keys(
    vault_name: str,
    load: Callable,
    default: int = 0,
) -> List[str]:
    """Return all vault keys sorted by priority (highest first)."""
    data = load(vault_name)
    priorities = _get_priorities(data)
    keys = [k for k in data if not k.startswith("__")]
    return sorted(keys, key=lambda k: priorities.get(k, default), reverse=True)
