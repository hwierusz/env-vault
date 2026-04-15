"""Tests for env_vault.impact."""
import pytest
from unittest.mock import patch

from env_vault.impact import analyze_impact, ImpactError, ImpactResult, _collect_reference_map, _transitive


VARS_SIMPLE = {
    "BASE_URL": "https://example.com",
    "API_URL": "${BASE_URL}/api",
    "CALLBACK": "${API_URL}/callback",
    "UNRELATED": "hello",
}


def _noop_deps(key, vars_):
    return []


def test_collect_reference_map_basic():
    ref_map = _collect_reference_map(VARS_SIMPLE)
    assert "BASE_URL" in ref_map
    assert "API_URL" in ref_map["BASE_URL"]


def test_collect_reference_map_no_refs():
    ref_map = _collect_reference_map({"FOO": "bar", "BAZ": "qux"})
    assert ref_map == {}


def test_transitive_empty():
    assert _transitive("X", {}) == []


def test_transitive_chain():
    dep_map = {"A": ["B"], "B": ["C"], "C": []}
    result = _transitive("A", dep_map)
    assert "B" in result
    assert "C" in result


def test_analyze_impact_missing_key_raises():
    with pytest.raises(ImpactError, match="not found"):
        with patch("env_vault.impact.list_dependencies", side_effect=_noop_deps):
            analyze_impact("MISSING", VARS_SIMPLE)


def test_analyze_impact_direct_reference():
    with patch("env_vault.impact.list_dependencies", return_value=[]):
        result = analyze_impact("BASE_URL", VARS_SIMPLE)
    assert isinstance(result, ImpactResult)
    assert "API_URL" in result.referenced_by


def test_analyze_impact_no_dependents():
    with patch("env_vault.impact.list_dependencies", return_value=[]):
        result = analyze_impact("UNRELATED", VARS_SIMPLE)
    assert result.direct_dependents == []
    assert result.transitive_dependents == []
    assert result.referenced_by == []


def test_analyze_impact_total_affected():
    with patch("env_vault.impact.list_dependencies", return_value=[]):
        result = analyze_impact("BASE_URL", VARS_SIMPLE)
    assert result.total_affected >= 1


def test_analyze_impact_transitive():
    with patch("env_vault.impact.list_dependencies", return_value=[]):
        result = analyze_impact("BASE_URL", VARS_SIMPLE)
    # CALLBACK references API_URL which references BASE_URL — transitive hit
    all_affected = set(result.direct_dependents) | set(result.transitive_dependents) | set(result.referenced_by)
    assert "CALLBACK" in all_affected or "API_URL" in all_affected


def test_analyze_impact_dependency_error_is_tolerated():
    """If list_dependencies raises, impact analysis should still return a result."""
    with patch("env_vault.impact.list_dependencies", side_effect=Exception("db error")):
        result = analyze_impact("BASE_URL", VARS_SIMPLE)
    assert isinstance(result, ImpactResult)


def test_impact_result_repr_contains_key():
    r = ImpactResult(key="FOO", direct_dependents=["BAR"])
    assert "FOO" in repr(r)
