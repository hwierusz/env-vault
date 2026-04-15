"""Policy management: define, store, and evaluate named policies against vault variables."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from env_vault.enforce import EnforceError, available_policies, run_policy


class PolicyError(Exception):
    """Raised when a policy operation fails."""


@dataclass
class PolicyResult:
    policy: str
    passed: bool
    violations: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        status = "PASS" if self.passed else "FAIL"
        return f"<PolicyResult policy={self.policy!r} status={status} violations={len(self.violations)}>"


def _get_policy_section(data: dict) -> dict:
    return data.setdefault("__policies__", {})


def assign_policy(data: dict, vault_name: str, policy_name: str) -> None:
    """Assign a named policy to a vault."""
    if policy_name not in available_policies():
        raise PolicyError(f"Unknown policy: {policy_name!r}")
    section = _get_policy_section(data)
    policies = section.setdefault(vault_name, [])
    if policy_name not in policies:
        policies.append(policy_name)


def unassign_policy(data: dict, vault_name: str, policy_name: str) -> None:
    """Remove a named policy from a vault."""
    section = _get_policy_section(data)
    policies = section.get(vault_name, [])
    if policy_name not in policies:
        raise PolicyError(f"Policy {policy_name!r} not assigned to {vault_name!r}")
    policies.remove(policy_name)


def list_policies_for(data: dict, vault_name: str) -> List[str]:
    """Return all policies assigned to a vault."""
    section = _get_policy_section(data)
    return list(section.get(vault_name, []))


def evaluate_policies(data: dict, vault_name: str) -> List[PolicyResult]:
    """Run all assigned policies against the vault variables and return results."""
    vars_ = {k: v for k, v in data.items() if not k.startswith("__")}
    assigned = list_policies_for(data, vault_name)
    results: List[PolicyResult] = []
    for policy_name in assigned:
        violations = run_policy(policy_name, vars_)
        results.append(PolicyResult(
            policy=policy_name,
            passed=len(violations) == 0,
            violations=violations,
        ))
    return results
