"""Placeholder detection and resolution for env-vault.

Allows vault values to reference other vault keys using ${KEY} syntax.
"""

import re
from typing import Dict, List, Optional

_REF_PATTERN = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)\}")


class PlaceholderError(Exception):
    pass


def collect_references(value: str) -> List[str]:
    """Return all referenced key names found in a value string."""
    return _REF_PATTERN.findall(value)


def resolve_value(value: str, vars: Dict[str, str], *, depth: int = 0) -> str:
    """Recursively resolve ${KEY} references in value using vars dict.

    Raises PlaceholderError on missing keys or circular depth limit.
    """
    if depth > 10:
        raise PlaceholderError("Maximum reference depth exceeded (possible circular reference)")

    def _replace(match: re.Match) -> str:
        key = match.group(1)
        if key not in vars:
            raise PlaceholderError(f"Referenced key '{key}' not found in vault")
        return resolve_value(vars[key], vars, depth=depth + 1)

    return _REF_PATTERN.sub(_replace, value)


def resolve_all(vars: Dict[str, str]) -> Dict[str, str]:
    """Return a new dict with all placeholder references resolved.

    Raises PlaceholderError if any reference is missing or circular.
    """
    resolved: Dict[str, str] = {}
    for key, value in vars.items():
        resolved[key] = resolve_value(value, vars)
    return resolved


def has_references(value: str) -> bool:
    """Return True if the value contains any ${KEY} references."""
    return bool(_REF_PATTERN.search(value))


def unresolved_references(vars: Dict[str, str]) -> Dict[str, List[str]]:
    """Return a mapping of key -> list of unresolvable references."""
    result: Dict[str, List[str]] = {}
    for key, value in vars.items():
        missing = [ref for ref in collect_references(value) if ref not in vars]
        if missing:
            result[key] = missing
    return result
