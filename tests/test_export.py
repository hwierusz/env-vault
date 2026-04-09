"""Tests for env_vault.export module."""

import json
import pytest

from env_vault.export import export_vars, import_vars


SAMPLE = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "p@ss w0rd"}


# ---------------------------------------------------------------------------
# export_vars
# ---------------------------------------------------------------------------

def test_export_dotenv_format():
    result = export_vars({"KEY": "value"}, fmt="dotenv")
    assert "KEY=value" in result


def test_export_dotenv_quotes_values_with_spaces():
    result = export_vars({"MSG": "hello world"}, fmt="dotenv")
    assert 'MSG="hello world"' in result


def test_export_json_format():
    result = export_vars({"A": "1"}, fmt="json")
    parsed = json.loads(result)
    assert parsed == {"A": "1"}


def test_export_shell_format():
    result = export_vars({"PATH_EXT": "/usr/bin"}, fmt="shell")
    assert result.startswith("export ")
    assert "PATH_EXT='/usr/bin'" in result


def test_export_unsupported_format_raises():
    with pytest.raises(ValueError, match="Unsupported format"):
        export_vars({"K": "v"}, fmt="xml")


def test_export_sorted_keys():
    result = export_vars({"Z": "z", "A": "a"}, fmt="dotenv")
    assert result.index("A=") < result.index("Z=")


# ---------------------------------------------------------------------------
# import_vars
# ---------------------------------------------------------------------------

def test_import_dotenv_simple():
    content = "KEY=value\nOTHER=123"
    result = import_vars(content, fmt="dotenv")
    assert result == {"KEY": "value", "OTHER": "123"}


def test_import_dotenv_skips_comments():
    content = "# comment\nKEY=value"
    result = import_vars(content, fmt="dotenv")
    assert "KEY" in result
    assert len(result) == 1


def test_import_dotenv_strips_quotes():
    content = 'MSG="hello world"'
    result = import_vars(content, fmt="dotenv")
    assert result["MSG"] == "hello world"


def test_import_shell_format():
    content = "export FOO='bar'\nexport BAZ=qux"
    result = import_vars(content, fmt="shell")
    assert result["FOO"] == "bar"
    assert result["BAZ"] == "qux"


def test_import_json_format():
    content = json.dumps({"X": "1", "Y": "2"})
    result = import_vars(content, fmt="json")
    assert result == {"X": "1", "Y": "2"}


def test_import_json_non_dict_raises():
    with pytest.raises(ValueError, match="top-level object"):
        import_vars("[1, 2, 3]", fmt="json")


def test_roundtrip_dotenv():
    exported = export_vars(SAMPLE, fmt="dotenv")
    imported = import_vars(exported, fmt="dotenv")
    assert imported == SAMPLE


def test_roundtrip_json():
    exported = export_vars(SAMPLE, fmt="json")
    imported = import_vars(exported, fmt="json")
    assert imported == SAMPLE
