"""Tests for env_vault.compress."""

import gzip
import json
import pytest

from env_vault.compress import (
    compress_vault,
    decompress_vault,
    compression_ratio,
    CompressError,
)


SAMPLE: dict = {
    "vars": {
        "DATABASE_URL": "postgres://localhost/mydb",
        "SECRET_KEY": "supersecretvalue",
        "DEBUG": "false",
    }
}


def test_compress_returns_bytes():
    result = compress_vault(SAMPLE)
    assert isinstance(result, bytes)


def test_compressed_is_valid_gzip():
    blob = compress_vault(SAMPLE)
    # gzip magic bytes
    assert blob[:2] == b"\x1f\x8b"


def test_decompress_roundtrip():
    blob = compress_vault(SAMPLE)
    recovered = decompress_vault(blob)
    assert recovered == SAMPLE


def test_decompress_invalid_bytes_raises():
    with pytest.raises(CompressError):
        decompress_vault(b"not-gzip-data")


def test_decompress_valid_gzip_invalid_json_raises():
    bad_blob = gzip.compress(b"not-json")
    with pytest.raises(CompressError):
        decompress_vault(bad_blob)


def test_compress_empty_dict():
    blob = compress_vault({})
    assert decompress_vault(blob) == {}


def test_compression_ratio_below_one_for_repetitive_data():
    large = {"vars": {f"KEY_{i}": "value" * 20 for i in range(50)}}
    ratio = compression_ratio(large)
    assert ratio < 1.0


def test_compression_ratio_empty_returns_zero():
    ratio = compression_ratio({})
    assert ratio == 0.0


def test_compression_ratio_is_float():
    ratio = compression_ratio(SAMPLE)
    assert isinstance(ratio, float)


def test_compress_non_serialisable_raises():
    with pytest.raises(CompressError):
        compress_vault({"bad": object()})  # type: ignore[dict-item]
