"""Visibility control for vault variables (public / private / hidden)."""

from __future__ import annotations

from typing import Dict, List, Optional

VISIBILITY_LEVELS = ("public", "private", "hidden")


class VisibilityError(Exception):
    pass


def _get_visibility_section(data: dict) -> dict:
    return data.setdefault("__visibility__", {})


def set_visibility(data: dict, key: str, level: str) -> None:
    """Set the visibility level for *key*.

    Raises VisibilityError if *key* is not in the vault or *level* is invalid.
    """
    if key not in data.get("vars", {}):
        raise VisibilityError(f"Key '{key}' not found in vault.")
    if level not in VISIBILITY_LEVELS:
        raise VisibilityError(
            f"Invalid visibility level '{level}'. "
            f"Choose from: {', '.join(VISIBILITY_LEVELS)}"
        )
    _get_visibility_section(data)[key] = level


def get_visibility(data: dict, key: str) -> str:
    """Return the visibility level for *key* (defaults to 'private')."""
    return _get_visibility_section(data).get(key, "private")


def remove_visibility(data: dict, key: str) -> None:
    """Remove an explicit visibility setting, reverting to the default."""
    section = _get_visibility_section(data)
    if key not in section:
        raise VisibilityError(f"No visibility setting found for key '{key}'.")
    del section[key]


def filter_by_visibility(
    data: dict,
    level: str,
    *,
    include_higher: bool = False,
) -> Dict[str, str]:
    """Return vars whose visibility matches *level*.

    If *include_higher* is True, 'public' also appears when filtering for
    'private', and both appear when filtering for 'hidden'.
    """
    if level not in VISIBILITY_LEVELS:
        raise VisibilityError(f"Invalid visibility level '{level}'.")
    order = list(VISIBILITY_LEVELS)
    cutoff = order.index(level)
    allowed: List[str] = order[: cutoff + 1] if include_higher else [level]
    section = _get_visibility_section(data)
    vars_ = data.get("vars", {})
    return {
        k: v
        for k, v in vars_.items()
        if section.get(k, "private") in allowed
    }


def list_visibility(data: dict) -> Dict[str, str]:
    """Return a mapping of every key that has an explicit visibility setting."""
    return dict(_get_visibility_section(data))
