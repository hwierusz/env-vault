"""env_type.py — Assign and retrieve environment types for vault keys.

Supported types: string, integer, boolean, float, json
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional

VALID_TYPES = ("string", "integer", "boolean", "float", "json")

_COERCE: Dict[str, Callable[[str], Any]] = {
    "string": str,
    "integer": int,
    "boolean": lambda v: v.lower() in ("1", "true", "yes", "on"),
    "float": float,
    "json": __import__("json").loads,
}


class EnvTypeError(Exception):
    """Raised when an env-type operation fails."""


def _get_types_section(data: dict) -> dict:
    return data.setdefault("__env_types__", {})


def set_type(data: dict, key: str, type_name: str) -> None:
    """Assign *type_name* to *key* inside *data*."""
    if key not in data.get("vars", {}):
        raise EnvTypeError(f"Key '{key}' does not exist in the vault.")
    if type_name not in VALID_TYPES:
        raise EnvTypeError(
            f"Unknown type '{type_name}'. Valid types: {', '.join(VALID_TYPES)}"
        )
    _get_types_section(data)[key] = type_name


def get_type(data: dict, key: str) -> Optional[str]:
    """Return the declared type for *key*, or None if unset."""
    return _get_types_section(data).get(key)


def remove_type(data: dict, key: str) -> None:
    """Remove the type declaration for *key*."""
    section = _get_types_section(data)
    if key not in section:
        raise EnvTypeError(f"No type declared for key '{key}'.")
    del section[key]


def coerce_value(data: dict, key: str) -> Any:
    """Return the value of *key* coerced to its declared type.

    Raises EnvTypeError if no type is declared or coercion fails.
    """
    type_name = get_type(data, key)
    if type_name is None:
        raise EnvTypeError(f"No type declared for key '{key}'.")
    raw = data.get("vars", {}).get(key)
    if raw is None:
        raise EnvTypeError(f"Key '{key}' not found in vault vars.")
    try:
        return _COERCE[type_name](raw)
    except (ValueError, TypeError, __import__("json").JSONDecodeError) as exc:
        raise EnvTypeError(
            f"Cannot coerce '{raw}' to {type_name}: {exc}"
        ) from exc


def list_typed_keys(data: dict) -> Dict[str, str]:
    """Return a mapping of key -> type for all typed keys."""
    return dict(_get_types_section(data))
