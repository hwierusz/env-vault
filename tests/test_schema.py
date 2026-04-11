"""Tests for env_vault.schema."""
import pytest

from env_vault.schema import (
    SchemaError,
    SchemaRule,
    rules_from_dict,
    validate_vars,
)


# ---------------------------------------------------------------------------
# SchemaRule.validate
# ---------------------------------------------------------------------------

def test_required_key_missing_produces_error():
    rule = SchemaRule(key="API_KEY", required=True)
    errors = rule.validate(None)
    assert len(errors) == 1
    assert "required" in errors[0]


def test_optional_key_missing_produces_no_error():
    rule = SchemaRule(key="API_KEY", required=False)
    assert rule.validate(None) == []


def test_pattern_match_passes():
    rule = SchemaRule(key="PORT", pattern=r"\d+")
    assert rule.validate("8080") == []


def test_pattern_mismatch_produces_error():
    rule = SchemaRule(key="PORT", pattern=r"\d+")
    errors = rule.validate("abc")
    assert len(errors) == 1
    assert "pattern" in errors[0]


def test_min_length_violation():
    rule = SchemaRule(key="SECRET", min_length=8)
    errors = rule.validate("short")
    assert any("too short" in e for e in errors)


def test_max_length_violation():
    rule = SchemaRule(key="CODE", max_length=4)
    errors = rule.validate("toolongvalue")
    assert any("too long" in e for e in errors)


def test_allowed_values_pass():
    rule = SchemaRule(key="ENV", allowed_values=["dev", "prod", "staging"])
    assert rule.validate("prod") == []


def test_allowed_values_violation():
    rule = SchemaRule(key="ENV", allowed_values=["dev", "prod"])
    errors = rule.validate("unknown")
    assert any("allowed" in e for e in errors)


# ---------------------------------------------------------------------------
# validate_vars
# ---------------------------------------------------------------------------

def test_validate_vars_clean():
    rules = [SchemaRule(key="HOST", required=True), SchemaRule(key="PORT", pattern=r"\d+")]
    assert validate_vars({"HOST": "localhost", "PORT": "5432"}, rules) == []


def test_validate_vars_collects_all_violations():
    rules = [
        SchemaRule(key="HOST", required=True),
        SchemaRule(key="PORT", pattern=r"\d+"),
    ]
    violations = validate_vars({"PORT": "bad"}, rules)
    assert len(violations) == 2  # HOST missing + PORT pattern


# ---------------------------------------------------------------------------
# rules_from_dict
# ---------------------------------------------------------------------------

def test_rules_from_dict_basic():
    raw = [{"key": "API_KEY", "required": True, "min_length": 10}]
    rules = rules_from_dict(raw)
    assert len(rules) == 1
    assert rules[0].key == "API_KEY"
    assert rules[0].required is True
    assert rules[0].min_length == 10


def test_rules_from_dict_missing_key_raises():
    with pytest.raises(SchemaError):
        rules_from_dict([{"required": True}])


def test_rules_from_dict_defaults():
    rules = rules_from_dict([{"key": "X"}])
    r = rules[0]
    assert r.required is False
    assert r.pattern is None
    assert r.allowed_values == []
