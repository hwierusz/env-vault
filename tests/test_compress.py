import gzip
import json
import pytest
from env_vault.compress import compress_vault, decompress_vault, compression_ratio, CompressError


SAMPLE = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET_KEY": "s3cr3t"}


def test_compress_returns_bytes():
    result = compress_vault(SAMPLE)
    assert isinstance(result, bytes)


def test_compressed_is_valid_gzip():
    result = compress_vault(SAMPLE)
    # gzip magic bytes
    assert result[:2] == b"\x1f\x8b"


def test_decompress_roundtrip():
    compressed = compress_vault(SAMPLE)
    recovered = decompress_vault(compressed)
    assert recovered == SAMPLE


def test_decompress_invalid_bytes_raises():
    with pytest.raises(CompressError, match="decompress"):
        decompress_vault(b"not gzip data at all")


def test_decompress_valid_gzip_invalid_json_raises():
    bad = gzip.compress(b"not json!!!")
    with pytest.raises(CompressError, match="valid JSON"):
        decompress_vault(bad)


def test_decompress_json_array_raises():
    bad = gzip.compress(json.dumps(["a", "b"]).encode())
    with pytest.raises(CompressError, match="JSON object"):
        decompress_vault(bad)


def test_compression_ratio_is_float():
    ratio = compression_ratio(SAMPLE)
    assert isinstance(ratio, float)


def test_compression_ratio_less_than_one_for_large_data():
    large = {f"KEY_{i}": "value" * 20 for i in range(50)}
    ratio = compression_ratio(large)
    assert ratio < 1.0


def test_compression_ratio_empty_dict_returns_one():
    ratio = compression_ratio({})
    assert ratio == 1.0


def test_compress_empty_dict_roundtrip():
    compressed = compress_vault({})
    recovered = decompress_vault(compressed)
    assert recovered == {}


def test_compress_special_characters():
    data = {"MSG": "hello\nworld\ttab", "UNICODE": "caf\u00e9"}
    recovered = decompress_vault(compress_vault(data))
    assert recovered == data
