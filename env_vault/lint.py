"""Lint/validate environment variable keys and values in a vault."""

import re
from typing import Dict, List

POSIX_KEY_RE = re.compile(r'^[A-Z_][A-Z0-9_]*$')
MAX_VALUE_LENGTH = 4096
MAX_KEY_LENGTH = 128


class LintError(Exception):
    """Raised when lint encounters a fatal problem (e.g. vault missing)."""


class LintWarning:
    """Represents a single lint finding."""

    def __init__(self, key: str, message: str, severity: str = "warning"):
        self.key = key
        self.message = message
        self.severity = severity  # 'warning' | 'error'

    def __repr__(self) -> str:  # pragma: no cover
        return f"LintWarning({self.severity!r}, {self.key!r}: {self.message!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LintWarning):
            return NotImplemented
        return (self.key, self.message, self.severity) == (
            other.key,
            other.message,
            other.severity,
        )


def lint_vars(
    variables: Dict[str, str],
    *,
    strict_keys: bool = True,
    warn_empty_values: bool = True,
    warn_long_values: bool = True,
) -> List[LintWarning]:
    """Analyse *variables* and return a list of :class:`LintWarning` objects.

    Parameters
    ----------
    variables:
        Mapping of key -> value as returned by :func:`load_vault`.
    strict_keys:
        When *True* (default) flag keys that don't follow the POSIX
        convention of ``UPPER_SNAKE_CASE``.
    warn_empty_values:
        When *True* (default) flag keys whose value is an empty string.
    warn_long_values:
        When *True* (default) flag values that exceed ``MAX_VALUE_LENGTH``
        characters.
    """
    findings: List[LintWarning] = []

    for key, value in variables.items():
        # Key length
        if len(key) > MAX_KEY_LENGTH:
            findings.append(
                LintWarning(key, f"Key exceeds {MAX_KEY_LENGTH} characters.", "error")
            )

        # POSIX naming
        if strict_keys and not POSIX_KEY_RE.match(key):
            findings.append(
                LintWarning(
                    key,
                    "Key does not follow POSIX convention (UPPER_SNAKE_CASE).",
                    "warning",
                )
            )

        # Empty value
        if warn_empty_values and value == "":
            findings.append(LintWarning(key, "Value is empty.", "warning"))

        # Long value
        if warn_long_values and len(value) > MAX_VALUE_LENGTH:
            findings.append(
                LintWarning(
                    key,
                    f"Value exceeds {MAX_VALUE_LENGTH} characters.",
                    "warning",
                )
            )

    return findings
