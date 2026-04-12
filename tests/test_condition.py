"""Tests for env_vault.condition."""
import pytest

from env_vault.condition import (
    ConditionError,
    ConditionRule,
    apply_conditions,
    evaluate_condition,
    rules_from_list,
)


# ---------------------------------------------------------------------------
# evaluate_condition
# ---------------------------------------------------------------------------

def test_eq_true():
    rule = ConditionRule(key="ENV", op="eq", value="prod")
    assert evaluate_condition(rule, {"ENV": "prod"}) is True


def test_eq_false():
    rule = ConditionRule(key="ENV", op="eq", value="prod")
    assert evaluate_condition(rule, {"ENV": "dev"}) is False


def test_neq_true():
    rule = ConditionRule(key="ENV", op="neq", value="prod")
    assert evaluate_condition(rule, {"ENV": "dev"}) is True


def test_contains_true():
    rule = ConditionRule(key="URL", op="contains", value="localhost")
    assert evaluate_condition(rule, {"URL": "http://localhost:8080"}) is True


def test_contains_false():
    rule = ConditionRule(key="URL", op="contains", value="prod")
    assert evaluate_condition(rule, {"URL": "http://localhost:8080"}) is False


def test_startswith_true():
    rule = ConditionRule(key="HOST", op="startswith", value="db")
    assert evaluate_condition(rule, {"HOST": "db.internal"}) is True


def test_endswith_true():
    rule = ConditionRule(key="HOST", op="endswith", value=".internal")
    assert evaluate_condition(rule, {"HOST": "db.internal"}) is True


def test_exists_true():
    rule = ConditionRule(key="API_KEY", op="exists")
    assert evaluate_condition(rule, {"API_KEY": "abc"}) is True


def test_exists_false_when_missing():
    rule = ConditionRule(key="API_KEY", op="exists")
    assert evaluate_condition(rule, {}) is False


def test_missing_key_returns_false_for_eq():
    rule = ConditionRule(key="MISSING", op="eq", value="x")
    assert evaluate_condition(rule, {}) is False


def test_unknown_op_raises():
    rule = ConditionRule(key="X", op="unknown", value="y")
    with pytest.raises(ConditionError, match="Unsupported operator"):
        evaluate_condition(rule, {"X": "y"})


# ---------------------------------------------------------------------------
# apply_conditions
# ---------------------------------------------------------------------------

def _make_loader(vault_vars):
    def _load(name):
        return {"vars": vault_vars}
    return _load


def test_apply_conditions_returns_overrides_when_rule_matches():
    rules = [ConditionRule(key="ENV", op="eq", value="prod", result="LOG_LEVEL=error")]
    loader = _make_loader({"LOG_LEVEL": "info"})
    overrides = apply_conditions(rules, {"ENV": "prod"}, loader, "myvault")
    assert overrides == {"LOG_LEVEL": "error"}


def test_apply_conditions_no_override_when_rule_does_not_match():
    rules = [ConditionRule(key="ENV", op="eq", value="prod", result="LOG_LEVEL=error")]
    loader = _make_loader({})
    overrides = apply_conditions(rules, {"ENV": "dev"}, loader, "myvault")
    assert overrides == {}


def test_apply_conditions_invalid_result_raises():
    rules = [ConditionRule(key="ENV", op="eq", value="prod", result="=bad")]
    loader = _make_loader({})
    with pytest.raises(ConditionError, match="Invalid result"):
        apply_conditions(rules, {"ENV": "prod"}, loader, "myvault")


# ---------------------------------------------------------------------------
# rules_from_list
# ---------------------------------------------------------------------------

def test_rules_from_list_basic():
    raw = [{"key": "ENV", "op": "eq", "value": "prod", "result": "DEBUG=false"}]
    rules = rules_from_list(raw)
    assert len(rules) == 1
    assert rules[0].key == "ENV"
    assert rules[0].op == "eq"
    assert rules[0].result == "DEBUG=false"


def test_rules_from_list_defaults_op_to_eq():
    raw = [{"key": "X", "value": "1"}]
    rules = rules_from_list(raw)
    assert rules[0].op == "eq"
