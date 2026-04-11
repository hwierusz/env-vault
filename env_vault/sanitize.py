"""Sanitize environment variable keys and values before storing."""

import re
from typing import Dict, List, NamedTuple


class SanitizeError(Exception):
    pass


class SanitizeResult(NamedTuple):
    key: str
    original_key: str
    value: str
    original_value: str
    key_changed: bool
    value_changed: bool


_INVALID_KEY_CHARS = re.compile(r"[^A-Z0-9_]")
_LEADING_DIGIT = re.compile(r"^[0-9]")


def sanitize_key(key: str) -> str:
    """Normalize a key to uppercase, replacing invalid characters with '_'."""
    upper = key.upper()
    cleaned = _INVALID_KEY_CHARS.sub("_", upper)
    if _LEADING_DIGIT.match(cleaned):
        cleaned = "_" + cleaned
    return cleaned


def sanitize_value(value: str) -> str:
    """Strip leading/trailing whitespace and remove null bytes from a value."""
    return value.strip().replace("\x00", "")


def sanitize_entry(key: str, value: str) -> SanitizeResult:
    """Sanitize a single key/value pair, returning a SanitizeResult."""
    new_key = sanitize_key(key)
    new_value = sanitize_value(value)
    return SanitizeResult(
        key=new_key,
        original_key=key,
        value=new_value,
        original_value=value,
        key_changed=(new_key != key),
        value_changed=(new_value != value),
    )


def sanitize_vars(
    variables: Dict[str, str],
    strict: bool = False,
) -> Dict[str, str]:
    """Sanitize all keys and values in a dict.

    Args:
        variables: mapping of env var key -> value.
        strict: if True, raise SanitizeError when a key would be modified.

    Returns:
        A new dict with sanitized keys and values.

    Raises:
        SanitizeError: if strict=True and any key requires modification.
    """
    result: Dict[str, str] = {}
    for key, value in variables.items():
        entry = sanitize_entry(key, value)
        if strict and entry.key_changed:
            raise SanitizeError(
                f"Key {key!r} is not valid; would be renamed to {entry.key!r}. "
                "Fix the key or run without strict mode."
            )
        if entry.key in result:
            raise SanitizeError(
                f"Sanitized key collision: {entry.key!r} already exists "
                f"(from original key {key!r})."
            )
        result[entry.key] = entry.value
    return result


def find_dirty_keys(variables: Dict[str, str]) -> List[str]:
    """Return a list of keys that would be modified by sanitization."""
    return [k for k in variables if sanitize_key(k) != k]
