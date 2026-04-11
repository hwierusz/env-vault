"""Checksum utilities for detecting vault tampering or unexpected changes."""

import hashlib
import json
from typing import Dict, Optional


class ChecksumError(Exception):
    """Raised when checksum operations fail."""


def _stable_serialize(vars_dict: Dict[str, str]) -> bytes:
    """Serialize vars dict in a stable, deterministic way for hashing."""
    return json.dumps(vars_dict, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_checksum(vars_dict: Dict[str, str], algorithm: str = "sha256") -> str:
    """Compute a hex-digest checksum of the vault variables.

    Args:
        vars_dict: The key-value pairs from the vault.
        algorithm: Hash algorithm name (sha256, sha1, md5).

    Returns:
        Hex string digest.

    Raises:
        ChecksumError: If the algorithm is unsupported.
    """
    try:
        h = hashlib.new(algorithm)
    except ValueError:
        raise ChecksumError(f"Unsupported hash algorithm: {algorithm!r}")
    h.update(_stable_serialize(vars_dict))
    return h.hexdigest()


def verify_checksum(
    vars_dict: Dict[str, str],
    expected: str,
    algorithm: str = "sha256",
) -> bool:
    """Verify that the vault variables match an expected checksum.

    Args:
        vars_dict: Current vault key-value pairs.
        expected: Previously stored checksum hex string.
        algorithm: Hash algorithm used when the checksum was created.

    Returns:
        True if checksums match, False otherwise.
    """
    actual = compute_checksum(vars_dict, algorithm=algorithm)
    return actual == expected


def checksum_diff(
    vars_a: Dict[str, str],
    vars_b: Dict[str, str],
    algorithm: str = "sha256",
) -> Optional[str]:
    """Return the new checksum if vaults differ, or None if they are identical.

    Args:
        vars_a: Baseline vault variables.
        vars_b: Comparison vault variables.
        algorithm: Hash algorithm to use.

    Returns:
        Hex digest of vars_b if it differs from vars_a, else None.
    """
    cs_a = compute_checksum(vars_a, algorithm=algorithm)
    cs_b = compute_checksum(vars_b, algorithm=algorithm)
    return cs_b if cs_a != cs_b else None
