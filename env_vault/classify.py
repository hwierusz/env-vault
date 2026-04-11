"""Variable classification — categorise vault keys by sensitivity heuristics."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

# Patterns that suggest a secret / sensitive value
_SECRET_PATTERNS = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|private[_-]?key"
    r"|auth|credential|cert|passphrase|seed|salt|hmac|signing)",
    re.IGNORECASE,
)

# Patterns that suggest a URL or endpoint
_URL_PATTERNS = re.compile(r"(url|endpoint|host|uri|addr|address|base[_-]?path)", re.IGNORECASE)

# Patterns that suggest a numeric / flag config value
_CONFIG_PATTERNS = re.compile(r"(port|timeout|retry|limit|max|min|count|size|debug|verbose|level|mode)", re.IGNORECASE)


class ClassifyError(Exception):
    """Raised when classification cannot be performed."""


@dataclass
class ClassifyResult:
    key: str
    category: str  # 'secret' | 'url' | 'config' | 'unknown'
    confidence: float  # 0.0 – 1.0

    def __repr__(self) -> str:
        return f"ClassifyResult(key={self.key!r}, category={self.category!r}, confidence={self.confidence:.2f})"


def classify_key(key: str) -> ClassifyResult:
    """Classify a single key name and return a ClassifyResult."""
    if not isinstance(key, str) or not key.strip():
        raise ClassifyError("key must be a non-empty string")

    if _SECRET_PATTERNS.search(key):
        return ClassifyResult(key=key, category="secret", confidence=0.90)
    if _URL_PATTERNS.search(key):
        return ClassifyResult(key=key, category="url", confidence=0.85)
    if _CONFIG_PATTERNS.search(key):
        return ClassifyResult(key=key, category="config", confidence=0.80)
    return ClassifyResult(key=key, category="unknown", confidence=0.50)


def classify_vars(vars_dict: Dict[str, str]) -> List[ClassifyResult]:
    """Classify all keys in *vars_dict* and return a list of results sorted by key."""
    if not isinstance(vars_dict, dict):
        raise ClassifyError("vars_dict must be a dict")
    return [classify_key(k) for k in sorted(vars_dict)]


def summary(results: List[ClassifyResult]) -> Dict[str, int]:
    """Return a count per category from a list of ClassifyResult objects."""
    counts: Dict[str, int] = {}
    for r in results:
        counts[r.category] = counts.get(r.category, 0) + 1
    return counts
