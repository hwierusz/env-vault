"""Compression utilities for vault export/import to reduce storage size."""

import gzip
import json
import os
from typing import Dict, Any


class CompressError(Exception):
    pass


def compress_vault(data: Dict[str, Any]) -> bytes:
    """Serialize and gzip-compress vault data.

    Args:
        data: vault dictionary to compress.

    Returns:
        Compressed bytes.

    Raises:
        CompressError: if serialization or compression fails.
    """
    try:
        raw = json.dumps(data, separators=(",", ":")).encode("utf-8")
        return gzip.compress(raw, compresslevel=9)
    except (TypeError, ValueError) as exc:
        raise CompressError(f"Failed to compress vault data: {exc}") from exc


def decompress_vault(blob: bytes) -> Dict[str, Any]:
    """Decompress and deserialize vault data.

    Args:
        blob: gzip-compressed bytes.

    Returns:
        Vault dictionary.

    Raises:
        CompressError: if decompression or deserialization fails.
    """
    try:
        raw = gzip.decompress(blob)
        return json.loads(raw.decode("utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise CompressError(f"Failed to decompress vault data: {exc}") from exc


def compression_ratio(original: Dict[str, Any]) -> float:
    """Return the compression ratio (compressed / original) for given data.

    A value below 1.0 means compression reduced the size.

    Args:
        original: vault dictionary.

    Returns:
        Float ratio, e.g. 0.42 means 42 % of original size.
    """
    raw_size = len(json.dumps(original, separators=(",", ":")).encode("utf-8"))
    if raw_size == 0:
        return 0.0
    compressed_size = len(compress_vault(original))
    return compressed_size / raw_size
