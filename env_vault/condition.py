"""Conditional variable resolution based on simple rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


CONDITION_OPS = ("eq", "neq", "contains", "startswith", "endswith", "exists")


class ConditionError(Exception):
    """Raised when a condition cannot be evaluated."""


@dataclass
class ConditionRule:
    key: str
    op: str
    value: Optional[str] = None
    result: Optional[str] = None

    def __repr__(self) -> str:  # pragma: no cover
        return f"ConditionRule({self.key!r} {self.op} {self.value!r} -> {self.result!r})"


def _check(op: str, actual: Optional[str], expected: Optional[str]) -> bool:
    if op == "exists":
        return actual is not None
    if actual is None:
        return False
    if op == "eq":
        return actual == expected
    if op == "neq":
        return actual != expected
    if op == "contains":
        return expected is not None and expected in actual
    if op == "startswith":
        return expected is not None and actual.startswith(expected)
    if op == "endswith":
        return expected is not None and actual.endswith(expected)
    raise ConditionError(f"Unknown operator: {op!r}")


def evaluate_condition(
    rule: ConditionRule,
    vars_dict: Dict[str, str],
) -> bool:
    """Return True if the rule's condition is satisfied by vars_dict."""
    if rule.op not in CONDITION_OPS:
        raise ConditionError(f"Unsupported operator {rule.op!r}. Choose from {CONDITION_OPS}.")
    actual = vars_dict.get(rule.key)
    return _check(rule.op, actual, rule.value)


def apply_conditions(
    rules: List[ConditionRule],
    vars_dict: Dict[str, str],
    load_fn: Callable[[str], Dict[str, Any]],
    vault_name: str,
) -> Dict[str, str]:
    """Apply matching condition rules, returning overrides to merge into vars_dict."""
    data = load_fn(vault_name)
    env_vars: Dict[str, str] = data.get("vars", {})
    overrides: Dict[str, str] = {}
    for rule in rules:
        if evaluate_condition(rule, vars_dict):
            if rule.result is not None:
                key, _, val = rule.result.partition("=")
                key = key.strip()
                if not key:
                    raise ConditionError(f"Invalid result expression: {rule.result!r}")
                overrides[key] = val
    return overrides


def rules_from_list(raw: List[Dict[str, Any]]) -> List[ConditionRule]:
    """Build ConditionRule objects from a list of plain dicts."""
    rules = []
    for item in raw:
        op = item.get("op", "eq")
        rules.append(
            ConditionRule(
                key=item["key"],
                op=op,
                value=item.get("value"),
                result=item.get("result"),
            )
        )
    return rules
