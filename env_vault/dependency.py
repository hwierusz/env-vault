"""Dependency tracking between vault variables."""
from __future__ import annotations

from typing import Dict, List, Optional


class DependencyError(Exception):
    pass


def _get_deps(data: dict) -> dict:
    return data.setdefault("__dependencies__", {})


def add_dependency(
    data: dict,
    key: str,
    depends_on: str,
    load_fn=None,
    save_fn=None,
) -> None:
    """Record that *key* depends on *depends_on*."""
    vars_ = data.get("vars", {})
    if key not in vars_:
        raise DependencyError(f"Key '{key}' not found in vault.")
    if depends_on not in vars_:
        raise DependencyError(f"Key '{depends_on}' not found in vault.")
    if key == depends_on:
        raise DependencyError("A key cannot depend on itself.")
    deps = _get_deps(data)
    deps.setdefault(key, [])
    if depends_on not in deps[key]:
        deps[key].append(depends_on)
    if save_fn:
        save_fn(data)


def remove_dependency(data: dict, key: str, depends_on: str, save_fn=None) -> None:
    """Remove a recorded dependency."""
    deps = _get_deps(data)
    if key not in deps or depends_on not in deps[key]:
        raise DependencyError(f"Dependency '{key}' -> '{depends_on}' not found.")
    deps[key].remove(depends_on)
    if not deps[key]:
        del deps[key]
    if save_fn:
        save_fn(data)


def list_dependencies(data: dict, key: str) -> List[str]:
    """Return the list of keys that *key* depends on."""
    return list(_get_deps(data).get(key, []))


def dependents_of(data: dict, key: str) -> List[str]:
    """Return all keys that depend on *key*."""
    return [k for k, deps in _get_deps(data).items() if key in deps]


def resolve_order(data: dict) -> List[str]:
    """Return a topologically-sorted list of variable keys.

    Raises DependencyError on cycles.
    """
    vars_ = list(data.get("vars", {}).keys())
    deps = _get_deps(data)
    visited: Dict[str, str] = {}  # key -> 'visiting' | 'done'
    order: List[str] = []

    def visit(node: str) -> None:
        state = visited.get(node)
        if state == "done":
            return
        if state == "visiting":
            raise DependencyError(f"Circular dependency detected at '{node}'.")
        visited[node] = "visiting"
        for dep in deps.get(node, []):
            visit(dep)
        visited[node] = "done"
        order.append(node)

    for v in vars_:
        visit(v)
    return order
