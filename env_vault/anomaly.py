"""Anomaly detection for env-vault.

Detects unusual or suspicious patterns in vault variables such as
potential secrets stored in plaintext keys, duplicate values,
entropy anomalies, and structurally odd entries.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class AnomalyError(Exception):
    """Raised when anomaly detection cannot be completed."""


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class AnomalyResult:
    """Represents a single detected anomaly."""

    key: str
    anomaly_type: str
    detail: str
    severity: str = "warning"  # 'info' | 'warning' | 'critical'

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"AnomalyResult(key={self.key!r}, type={self.anomaly_type!r}, "
            f"severity={self.severity!r})"
        )

    def to_dict(self) -> Dict[str, str]:
        return {
            "key": self.key,
            "anomaly_type": self.anomaly_type,
            "detail": self.detail,
            "severity": self.severity,
        }


# ---------------------------------------------------------------------------
# Entropy helper
# ---------------------------------------------------------------------------

_MIN_HIGH_ENTROPY_LEN = 16
_HIGH_ENTROPY_THRESHOLD = 4.0  # bits per character (Shannon)


def _shannon_entropy(value: str) -> float:
    """Compute Shannon entropy (bits per character) for *value*."""
    if not value:
        return 0.0
    freq: Dict[str, int] = {}
    for ch in value:
        freq[ch] = freq.get(ch, 0) + 1
    length = len(value)
    return -sum((c / length) * math.log2(c / length) for c in freq.values())


# ---------------------------------------------------------------------------
# Individual detectors
# ---------------------------------------------------------------------------

_URL_PATTERN = re.compile(r"https?://[^\s]+", re.IGNORECASE)
_BEARER_PATTERN = re.compile(r"bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE)


def _detect_high_entropy(key: str, value: str) -> Optional[AnomalyResult]:
    """Flag values with suspiciously high entropy (possible raw secrets)."""
    if len(value) >= _MIN_HIGH_ENTROPY_LEN:
        entropy = _shannon_entropy(value)
        if entropy >= _HIGH_ENTROPY_THRESHOLD:
            return AnomalyResult(
                key=key,
                anomaly_type="high_entropy",
                detail=f"Value entropy {entropy:.2f} bits/char exceeds threshold {_HIGH_ENTROPY_THRESHOLD}",
                severity="warning",
            )
    return None


def _detect_embedded_url(key: str, value: str) -> Optional[AnomalyResult]:
    """Flag values that contain embedded URLs (possible credential leakage)."""
    if _URL_PATTERN.search(value):
        return AnomalyResult(
            key=key,
            anomaly_type="embedded_url",
            detail="Value contains an embedded URL which may include credentials",
            severity="info",
        )
    return None


def _detect_bearer_token(key: str, value: str) -> Optional[AnomalyResult]:
    """Flag values that look like raw Bearer tokens."""
    if _BEARER_PATTERN.match(value.strip()):
        return AnomalyResult(
            key=key,
            anomaly_type="bearer_token",
            detail="Value appears to be a raw Bearer token",
            severity="critical",
        )
    return None


def _detect_empty_value(key: str, value: str) -> Optional[AnomalyResult]:
    """Flag keys with empty or whitespace-only values."""
    if not value.strip():
        return AnomalyResult(
            key=key,
            anomaly_type="empty_value",
            detail="Value is empty or contains only whitespace",
            severity="warning",
        )
    return None


_DETECTORS: List[Callable[[str, str], Optional[AnomalyResult]]] = [
    _detect_empty_value,
    _detect_bearer_token,
    _detect_embedded_url,
    _detect_high_entropy,
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_anomalies(
    vars_: Dict[str, str],
    *,
    detectors: Optional[List[Callable[[str, str], Optional[AnomalyResult]]]] = None,
) -> List[AnomalyResult]:
    """Run all (or provided) detectors against *vars_* and return findings.

    Args:
        vars_: Mapping of variable key -> value to inspect.
        detectors: Optional list of detector callables to use instead of the
            built-in set.

    Returns:
        List of :class:`AnomalyResult` instances, one per detected anomaly.

    Raises:
        AnomalyError: If *vars_* is not a plain dict.
    """
    if not isinstance(vars_, dict):
        raise AnomalyError("vars_ must be a dict")

    active = detectors if detectors is not None else _DETECTORS
    results: List[AnomalyResult] = []

    for key, value in vars_.items():
        if not isinstance(value, str):
            # Skip non-string values silently
            continue
        for detector in active:
            finding = detector(key, value)
            if finding is not None:
                results.append(finding)

    return results


def detect_duplicates(vars_: Dict[str, str]) -> List[AnomalyResult]:
    """Detect keys that share identical values.

    Duplicate values can indicate copy-paste errors or misconfiguration.

    Args:
        vars_: Mapping of variable key -> value.

    Returns:
        List of :class:`AnomalyResult` instances for duplicate-value keys.
    """
    if not isinstance(vars_, dict):
        raise AnomalyError("vars_ must be a dict")

    value_map: Dict[str, List[str]] = {}
    for key, value in vars_.items():
        if isinstance(value, str):
            value_map.setdefault(value, []).append(key)

    results: List[AnomalyResult] = []
    for value, keys in value_map.items():
        if len(keys) > 1 and value.strip():  # ignore empty-value duplicates (already flagged)
            for key in keys:
                results.append(
                    AnomalyResult(
                        key=key,
                        anomaly_type="duplicate_value",
                        detail=f"Value shared with: {', '.join(k for k in keys if k != key)}",
                        severity="info",
                    )
                )

    return results


def available_detectors() -> List[str]:
    """Return names of built-in detector functions."""
    return sorted(d.__name__ for d in _DETECTORS)
