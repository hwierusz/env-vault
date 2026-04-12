import pytest
from env_vault.placeholder import (
    collect_references,
    resolve_value,
    resolve_all,
    has_references,
    unresolved_references,
    PlaceholderError,
)


def test_collect_references_basic():
    refs = collect_references("http://${HOST}:${PORT}/path")
    assert refs == ["HOST", "PORT"]


def test_collect_references_empty():
    assert collect_references("no refs here") == []


def test_collect_references_deduplicates_not():
    # collect_references returns all occurrences (not deduplicated)
    refs = collect_references("${A} and ${A}")
    assert refs == ["A", "A"]


def test_has_references_true():
    assert has_references("${SOME_KEY}") is True


def test_has_references_false():
    assert has_references("plain_value") is False


def test_resolve_value_simple():
    result = resolve_value("http://${HOST}", {"HOST": "localhost"})
    assert result == "http://localhost"


def test_resolve_value_multiple_refs():
    result = resolve_value("${PROTO}://${HOST}:${PORT}", {
        "PROTO": "https",
        "HOST": "example.com",
        "PORT": "8443",
    })
    assert result == "https://example.com:8443"


def test_resolve_value_no_refs():
    result = resolve_value("static_value", {})
    assert result == "static_value"


def test_resolve_value_missing_key_raises():
    with pytest.raises(PlaceholderError, match="'MISSING'"):
        resolve_value("${MISSING}", {})


def test_resolve_value_chained():
    vars = {"A": "hello", "B": "${A}_world"}
    result = resolve_value("${B}", vars)
    assert result == "hello_world"


def test_resolve_value_circular_raises():
    vars = {"A": "${B}", "B": "${A}"}
    with pytest.raises(PlaceholderError, match="depth"):
        resolve_value("${A}", vars)


def test_resolve_all_returns_full_dict():
    vars = {"BASE": "http://localhost", "URL": "${BASE}/api"}
    resolved = resolve_all(vars)
    assert resolved["URL"] == "http://localhost/api"
    assert resolved["BASE"] == "http://localhost"


def test_resolve_all_raises_on_missing():
    with pytest.raises(PlaceholderError):
        resolve_all({"KEY": "${UNDEFINED}"})


def test_unresolved_references_finds_missing():
    vars = {"A": "${B}", "C": "plain"}
    missing = unresolved_references(vars)
    assert missing == {"A": ["B"]}


def test_unresolved_references_empty_when_all_present():
    vars = {"A": "val", "B": "${A}"}
    assert unresolved_references(vars) == {}


def test_unresolved_references_multiple_missing():
    vars = {"X": "${Y}_${Z}"}
    missing = unresolved_references(vars)
    assert set(missing["X"]) == {"Y", "Z"}
