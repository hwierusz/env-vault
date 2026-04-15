"""digest.py — compute and verify a cryptographic digest (HMAC-SHA256) for a vault.

Provides tamper-detection: callers can store the digest alongside a vault and
later verify that the contents have not changed outside of env-vault.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Dict


class DigestError(Exception):
    """Raised when digest operations fail."""


def _stable_serialize(vars_: Dict[str, str]) -> bytes:
    """Return a deterministic JSON encoding of *vars_* (keys sorted)."""
    return json.dumps(vars_, sort_keys=True, separators=(",", ":")).encode()


def compute_digest(vars_: Dict[str, str], secret: str) -> str:
    """Return a hex HMAC-SHA256 digest of *vars_* keyed with *secret*.

    The digest is computed over a stable (sorted-key) JSON serialisation so
    that insertion order does not affect the result.

    Args:
        vars_: Mapping of environment variable names to values.
        secret: Shared secret used as the HMAC key.

    Returns:
        Lowercase hex string (64 characters).

    Raises:
        DigestError: If *vars_* is not a dict or *secret* is empty.
    """
    if not isinstance(vars_, dict):
        raise DigestError("vars_ must be a dict")
    if not secret:
        raise DigestError("secret must not be empty")

    payload = _stable_serialize(vars_)
    key = secret.encode()
    return hmac.new(key, payload, hashlib.sha256).hexdigest()


def verify_digest(vars_: Dict[str, str], secret: str, expected: str) -> bool:
    """Return True if the digest of *vars_* matches *expected*.

    Uses :func:`hmac.compare_digest` to prevent timing attacks.

    Args:
        vars_: Current vault contents.
        secret: Shared secret used when the digest was computed.
        expected: Previously stored digest hex string.

    Returns:
        True if the digest matches, False otherwise.

    Raises:
        DigestError: Propagated from :func:`compute_digest`.
    """
    actual = compute_digest(vars_, secret)
    return hmac.compare_digest(actual, expected.lower())


def digest_changed(vars_: Dict[str, str], secret: str, stored: str) -> bool:
    """Convenience inverse of :func:`verify_digest`."""
    return not verify_digest(vars_, secret, stored)
