"""Value transformation pipeline for env-vault."""

from __future__ import annotations

import re
from typing import Callable, Dict, List, Optional


class TransformError(Exception):
    """Raised when a transformation fails."""


# Built-in transformers

def _to_upper(value: str) -> str:
    return value.upper()


def _to_lower(value: str) -> str:
    return value.lower()


def _strip(value: str) -> str:
    return value.strip()


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def _mask(value: str) -> str:
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + "*" * (len(value) - 4) + value[-2:]


def _base64_encode(value: str) -> str:
    import base64
    return base64.b64encode(value.encode()).decode()


def _base64_decode(value: str) -> str:
    import base64
    try:
        return base64.b64decode(value.encode()).decode()
    except Exception as exc:
        raise TransformError(f"base64_decode failed: {exc}") from exc


_BUILTIN: Dict[str, Callable[[str], str]] = {
    "upper": _to_upper,
    "lower": _to_lower,
    "strip": _strip,
    "strip_quotes": _strip_quotes,
    "mask": _mask,
    "base64_encode": _base64_encode,
    "base64_decode": _base64_decode,
}


def available_transforms() -> List[str]:
    """Return names of all registered transformations."""
    return sorted(_BUILTIN.keys())


def apply_transform(value: str, name: str) -> str:
    """Apply a single named transform to *value*."""
    if name not in _BUILTIN:
        raise TransformError(
            f"Unknown transform '{name}'. Available: {', '.join(available_transforms())}"
        )
    return _BUILTIN[name](value)


def apply_transforms(value: str, names: List[str]) -> str:
    """Apply a sequence of transforms to *value* in order."""
    for name in names:
        value = apply_transform(value, name)
    return value


def transform_vars(
    variables: Dict[str, str],
    names: List[str],
    keys: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Apply *names* transforms to *variables*, optionally limited to *keys*.

    Returns a new dict with transformed values; untouched keys are copied as-is.
    """
    result: Dict[str, str] = {}
    target_keys = set(keys) if keys is not None else set(variables.keys())
    for k, v in variables.items():
        if k in target_keys:
            result[k] = apply_transforms(v, names)
        else:
            result[k] = v
    return result
