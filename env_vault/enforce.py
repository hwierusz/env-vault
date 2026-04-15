"""Built-in enforcement policies for vault variables."""
from __future__ import annotations

from typing import Callable, Dict, List


class EnforceError(Exception):
    """Raised when a policy lookup fails."""


class PolicyViolation:
    def __init__(self, key: str, message: str) -> None:
        self.key = key
        self.message = message

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PolicyViolation key={self.key!r} message={self.message!r}>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PolicyViolation):
            return NotImplemented
        return self.key == other.key and self.message == other.message


def _no_empty_values(vars_: Dict[str, str]) -> List[str]:
    return [f"{k}: value must not be empty" for k, v in vars_.items() if v == ""]


def _uppercase_keys(vars_: Dict[str, str]) -> List[str]:
    return [f"{k}: key must be uppercase" for k in vars_ if k != k.upper()]


def _no_spaces_in_keys(vars_: Dict[str, str]) -> List[str]:
    return [f"{k}: key must not contain spaces" for k in vars_ if " " in k]


def _no_leading_digit(vars_: Dict[str, str]) -> List[str]:
    return [f"{k}: key must not start with a digit" for k in vars_ if k and k[0].isdigit()]


_POLICIES: Dict[str, Callable[[Dict[str, str]], List[str]]] = {
    "no_empty_values": _no_empty_values,
    "uppercase_keys": _uppercase_keys,
    "no_spaces_in_keys": _no_spaces_in_keys,
    "no_leading_digit": _no_leading_digit,
}


def available_policies() -> List[str]:
    """Return sorted list of built-in policy names."""
    return sorted(_POLICIES.keys())


def run_policy(policy_name: str, vars_: Dict[str, str]) -> List[str]:
    """Run a named policy and return a list of violation messages."""
    if policy_name not in _POLICIES:
        raise EnforceError(f"Unknown policy: {policy_name!r}")
    return _POLICIES[policy_name](vars_)


def run_all_policies(vars_: Dict[str, str]) -> Dict[str, List[str]]:
    """Run all policies and return a mapping of policy name to violations."""
    return {name: fn(vars_) for name, fn in _POLICIES.items()}
