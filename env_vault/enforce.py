"""enforce.py — policy enforcement for vault variables."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


class EnforceError(Exception):
    """Raised when a policy cannot be applied."""


@dataclass
class PolicyViolation:
    key: str
    policy: str
    message: str

    def __repr__(self) -> str:  # pragma: no cover
        return f"PolicyViolation(key={self.key!r}, policy={self.policy!r})"


# Built-in policy predicates
def _no_empty_values(key: str, value: str) -> Optional[str]:
    if value.strip() == "":
        return "value must not be empty or whitespace"
    return None


def _uppercase_keys(key: str, value: str) -> Optional[str]:
    if key != key.upper():
        return "key must be uppercase"
    return None


def _no_spaces_in_keys(key: str, value: str) -> Optional[str]:
    if " " in key:
        return "key must not contain spaces"
    return None


_BUILTIN_POLICIES: Dict[str, Callable[[str, str], Optional[str]]] = {
    "no_empty_values": _no_empty_values,
    "uppercase_keys": _uppercase_keys,
    "no_spaces_in_keys": _no_spaces_in_keys,
}


def available_policies() -> List[str]:
    """Return names of all built-in policies."""
    return sorted(_BUILTIN_POLICIES.keys())


def enforce_policy(
    vars_: Dict[str, str],
    policies: List[str],
) -> List[PolicyViolation]:
    """Run *policies* against *vars_* and return all violations.

    Args:
        vars_: mapping of variable key -> value.
        policies: list of policy names to apply.

    Returns:
        List of PolicyViolation instances (empty when compliant).

    Raises:
        EnforceError: if an unknown policy name is given.
    """
    unknown = [p for p in policies if p not in _BUILTIN_POLICIES]
    if unknown:
        raise EnforceError(f"Unknown policies: {', '.join(unknown)}")

    violations: List[PolicyViolation] = []
    for policy_name in policies:
        check = _BUILTIN_POLICIES[policy_name]
        for key, value in vars_.items():
            msg = check(key, value)
            if msg is not None:
                violations.append(PolicyViolation(key=key, policy=policy_name, message=msg))
    return violations
