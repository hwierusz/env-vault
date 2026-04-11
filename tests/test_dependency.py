"""Tests for env_vault.dependency."""
import pytest
from env_vault.dependency import (
    DependencyError,
    add_dependency,
    remove_dependency,
    list_dependencies,
    dependents_of,
    resolve_order,
)


def _make_data(*keys):
    return {"vars": {k: f"val_{k}" for k in keys}}


def test_add_dependency_stores_entry():
    data = _make_data("A", "B")
    add_dependency(data, "A", "B")
    assert "B" in data["__dependencies__"]["A"]


def test_add_dependency_missing_key_raises():
    data = _make_data("A")
    with pytest.raises(DependencyError, match="'B' not found"):
        add_dependency(data, "A", "B")


def test_add_dependency_missing_source_raises():
    data = _make_data("B")
    with pytest.raises(DependencyError, match="'A' not found"):
        add_dependency(data, "A", "B")


def test_add_self_dependency_raises():
    data = _make_data("A")
    with pytest.raises(DependencyError, match="cannot depend on itself"):
        add_dependency(data, "A", "A")


def test_add_dependency_no_duplicates():
    data = _make_data("A", "B")
    add_dependency(data, "A", "B")
    add_dependency(data, "A", "B")
    assert data["__dependencies__"]["A"].count("B") == 1


def test_remove_dependency_cleans_entry():
    data = _make_data("A", "B")
    add_dependency(data, "A", "B")
    remove_dependency(data, "A", "B")
    assert "A" not in data["__dependencies__"]


def test_remove_nonexistent_dependency_raises():
    data = _make_data("A", "B")
    with pytest.raises(DependencyError, match="not found"):
        remove_dependency(data, "A", "B")


def test_list_dependencies_returns_list():
    data = _make_data("A", "B", "C")
    add_dependency(data, "A", "B")
    add_dependency(data, "A", "C")
    deps = list_dependencies(data, "A")
    assert set(deps) == {"B", "C"}


def test_list_dependencies_empty_for_no_deps():
    data = _make_data("A")
    assert list_dependencies(data, "A") == []


def test_dependents_of_returns_correct_keys():
    data = _make_data("A", "B", "C")
    add_dependency(data, "A", "C")
    add_dependency(data, "B", "C")
    result = dependents_of(data, "C")
    assert set(result) == {"A", "B"}


def test_resolve_order_no_deps():
    data = _make_data("X", "Y", "Z")
    order = resolve_order(data)
    assert set(order) == {"X", "Y", "Z"}


def test_resolve_order_respects_dependency():
    data = _make_data("A", "B")
    add_dependency(data, "A", "B")  # A depends on B => B should come first
    order = resolve_order(data)
    assert order.index("B") < order.index("A")


def test_resolve_order_detects_cycle():
    data = _make_data("A", "B")
    add_dependency(data, "A", "B")
    add_dependency(data, "B", "A")
    with pytest.raises(DependencyError, match="Circular"):
        resolve_order(data)


def test_save_fn_called_on_add():
    data = _make_data("A", "B")
    calls = []
    add_dependency(data, "A", "B", save_fn=lambda d: calls.append(True))
    assert calls


def test_save_fn_called_on_remove():
    data = _make_data("A", "B")
    add_dependency(data, "A", "B")
    calls = []
    remove_dependency(data, "A", "B", save_fn=lambda d: calls.append(True))
    assert calls
