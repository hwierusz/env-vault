"""Value formatting utilities for env-vault."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional


class FormatError(Exception):
    """Raised when a formatting operation fails."""


_FORMATTERS: Dict[str, Callable[[str], str]] = {
    "upper": str.upper,
    "lower": str.lower,
    "strip": str.strip,
    "title": str.title,
    "reverse": lambda v: v[::-1],
    "base64": lambda v: __import__("base64").b64encode(v.encode()).decode(),
    "base64decode": lambda v: __import__("base64").b64decode(v.encode()).decode(),
    "urlencode": lambda v: __import__("urllib.parse", fromlist=["quote"]).quote(v, safe=""),
    "urldecode": lambda v: __import__("urllib.parse", fromlist=["unquote"]).unquote(v),
    "len": lambda v: str(len(v)),
    "hex": lambda v: v.encode().hex(),
    "sha256": lambda v: __import__("hashlib").sha256(v.encode()).hexdigest(),
}


def available_formats() -> list[str]:
    """Return names of all registered formatters."""
    return sorted(_FORMATTERS.keys())


def format_value(value: str, fmt: str) -> str:
    """Apply a named format to *value*.

    Parameters
    ----------
    value:
        The string value to format.
    fmt:
        Name of the formatter to apply.

    Returns
    -------
    str
        The formatted string.

    Raises
    ------
    FormatError
        If *fmt* is not a recognised formatter name.
    """
    if fmt not in _FORMATTERS:
        raise FormatError(
            f"Unknown format '{fmt}'. Available: {', '.join(available_formats())}"
        )
    try:
        return _FORMATTERS[fmt](value)
    except Exception as exc:  # pragma: no cover
        raise FormatError(f"Format '{fmt}' failed: {exc}") from exc


def format_vars(
    vars_: Dict[str, str],
    fmt: str,
    *,
    keys: Optional[list[str]] = None,
) -> Dict[str, str]:
    """Apply *fmt* to every value in *vars_*, optionally restricted to *keys*.

    Returns a new dict; the original is not mutated.
    """
    target_keys = set(keys) if keys is not None else set(vars_)
    missing = target_keys - set(vars_)
    if missing:
        raise FormatError(
            f"Key(s) not found in vault: {', '.join(sorted(missing))}"
        )
    result = dict(vars_)
    for k in target_keys:
        result[k] = format_value(vars_[k], fmt)
    return result
