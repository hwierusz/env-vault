"""Impact analysis: determine which vaults/keys would be affected by changing a variable."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from env_vault.placeholder import collect_references
from env_vault.dependency import list_dependencies


class ImpactError(Exception):
    """Raised when impact analysis fails."""


@dataclass
class ImpactResult:
    key: str
    direct_dependents: List[str] = field(default_factory=list)
    transitive_dependents: List[str] = field(default_factory=list)
    referenced_by: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ImpactResult(key={self.key!r}, direct={self.direct_dependents}, "
            f"transitive={self.transitive_dependents}, refs={self.referenced_by})"
        )

    @property
    def total_affected(self) -> int:
        all_keys = set(self.direct_dependents) | set(self.transitive_dependents) | set(self.referenced_by)
        return len(all_keys)


def _collect_reference_map(vars_: Dict[str, str]) -> Dict[str, List[str]]:
    """Return mapping: key -> list of keys whose values reference it."""
    ref_map: Dict[str, List[str]] = {}
    for k, v in vars_.items():
        for ref in collect_references(v):
            ref_map.setdefault(ref, []).append(k)
    return ref_map


def _transitive(key: str, dep_map: Dict[str, List[str]], visited: Optional[set] = None) -> List[str]:
    if visited is None:
        visited = set()
    result = []
    for dep in dep_map.get(key, []):
        if dep not in visited:
            visited.add(dep)
            result.append(dep)
            result.extend(_transitive(dep, dep_map, visited))
    return result


def analyze_impact(
    key: str,
    vars_: Dict[str, str],
    load_fn: Optional[Callable[[str], Dict]] = None,
    vault_name: str = "default",
) -> ImpactResult:
    """Analyse which keys are affected if *key* changes."""
    if key not in vars_:
        raise ImpactError(f"Key {key!r} not found in vault {vault_name!r}")

    ref_map = _collect_reference_map(vars_)
    referenced_by = ref_map.get(key, [])

    raw_deps: Dict[str, List[str]] = {}
    try:
        deps = list_dependencies(key, vars_)
        for dep_key in deps:
            raw_deps.setdefault(dep_key, []).append(key)
    except Exception:
        deps = []

    direct = list(set(referenced_by + deps))

    dep_map: Dict[str, List[str]] = {}
    for k in vars_:
        dep_map[k] = ref_map.get(k, [])

    transitive = [t for t in _transitive(key, dep_map) if t not in direct]

    return ImpactResult(
        key=key,
        direct_dependents=direct,
        transitive_dependents=transitive,
        referenced_by=referenced_by,
    )
