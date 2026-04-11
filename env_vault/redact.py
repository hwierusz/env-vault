"""Redaction utilities for masking sensitive variable values in output."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Patterns that suggest a value should be redacted
_SENSITIVE_PATTERNS: List[re.Pattern] = [
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"api[_\-]?key", re.IGNORECASE),
    re.compile(r"private[_\-]?key", re.IGNORECASE),
    re.compile(r"auth", re.IGNORECASE),
    re.compile(r"credential", re.IGNORECASE),
    re.compile(r"passphrase", re.IGNORECASE),
]

DEFAULT_MASK = "***REDACTED***"
_PARTIAL_VISIBLE = 4  # characters to reveal at start/end for partial mode


class RedactError(Exception):
    """Raised when redaction encounters an invalid state."""


@dataclass
class RedactResult:
    key: str
    original: str
    redacted: str
    was_redacted: bool

    def __repr__(self) -> str:  # pragma: no cover
        return f"RedactResult(key={self.key!r}, was_redacted={self.was_redacted})"


def is_sensitive(key: str) -> bool:
    """Return True if the key name matches any sensitive pattern."""
    return any(p.search(key) for p in _SENSITIVE_PATTERNS)


def redact_value(
    value: str,
    *,
    partial: bool = False,
    mask: str = DEFAULT_MASK,
) -> str:
    """Mask *value* entirely or show a partial preview.

    Args:
        value: The plaintext value to redact.
        partial: If True, reveal the first and last few characters.
        mask: Replacement string used when *partial* is False.
    """
    if not value:
        return mask
    if partial:
        if len(value) <= _PARTIAL_VISIBLE * 2:
            return mask
        return value[:_PARTIAL_VISIBLE] + "..." + value[-_PARTIAL_VISIBLE:]
    return mask


def redact_vars(
    variables: Dict[str, str],
    *,
    extra_keys: Optional[List[str]] = None,
    partial: bool = False,
    mask: str = DEFAULT_MASK,
) -> List[RedactResult]:
    """Redact all sensitive variables in *variables*.

    Args:
        variables: Mapping of env var key -> plaintext value.
        extra_keys: Additional key names to treat as sensitive.
        partial: Forward to :func:`redact_value`.
        mask: Forward to :func:`redact_value`.

    Returns:
        List of :class:`RedactResult` for every key in *variables*.
    """
    sensitive_extra: List[str] = [k.lower() for k in (extra_keys or [])]
    results: List[RedactResult] = []
    for key, value in variables.items():
        sensitive = is_sensitive(key) or key.lower() in sensitive_extra
        redacted = redact_value(value, partial=partial, mask=mask) if sensitive else value
        results.append(RedactResult(key=key, original=value, redacted=redacted, was_redacted=sensitive))
    return results
