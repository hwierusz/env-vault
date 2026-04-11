import gzip
import json
from typing import Dict


class CompressError(Exception):
    pass


def compress_vault(variables: Dict[str, str]) -> bytes:
    """Serialize and gzip-compress a variables dict."""
    try:
        raw = json.dumps(variables, separators=(",", ":")).encode("utf-8")
        return gzip.compress(raw)
    except (TypeError, ValueError) as exc:
        raise CompressError(f"Failed to compress vault data: {exc}") from exc


def decompress_vault(data: bytes) -> Dict[str, str]:
    """Decompress and deserialize a gzip-compressed variables dict."""
    try:
        raw = gzip.decompress(data)
    except (OSError, EOFError) as exc:
        raise CompressError(f"Failed to decompress data: {exc}") from exc
    try:
        result = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise CompressError(f"Decompressed data is not valid JSON: {exc}") from exc
    if not isinstance(result, dict):
        raise CompressError("Decompressed data must be a JSON object")
    return result


def compression_ratio(variables: Dict[str, str]) -> float:
    """Return the ratio of compressed size to original size (lower is better)."""
    try:
        original = json.dumps(variables, separators=(",", ":")).encode("utf-8")
        compressed = gzip.compress(original)
        if not original:
            return 1.0
        return len(compressed) / len(original)
    except (TypeError, ValueError) as exc:
        raise CompressError(f"Failed to compute compression ratio: {exc}") from exc
