"""Tests for env_vault.policy."""
import pytest

from env_vault.policy import (
    PolicyError,
    PolicyResult,
    assign_policy,
    unassign_policy,
    list_policies_for,
    evaluate_policies,
)


def _base_data():
    return {"DB_HOST": "localhost", "DB_PORT": "5432"}


def test_assign_policy_stores_entry():
    data = _base_data()
    assign_policy(data, "default", "uppercase_keys")
    assert "uppercase_keys" in data["__policies__"]["default"]


def test_assign_unknown_policy_raises():
    data = _base_data()
    with pytest.raises(PolicyError, match="Unknown policy"):
        assign_policy(data, "default", "nonexistent_policy")


def test_assign_duplicate_is_idempotent():
    data = _base_data()
    assign_policy(data, "default", "uppercase_keys")
    assign_policy(data, "default", "uppercase_keys")
    assert data["__policies__"]["default"].count("uppercase_keys") == 1


def test_unassign_removes_policy():
    data = _base_data()
    assign_policy(data, "default", "uppercase_keys")
    unassign_policy(data, "default", "uppercase_keys")
    assert "uppercase_keys" not in data["__policies__"].get("default", [])


def test_unassign_missing_policy_raises():
    data = _base_data()
    with pytest.raises(PolicyError, match="not assigned"):
        unassign_policy(data, "default", "uppercase_keys")


def test_list_policies_for_returns_assigned():
    data = _base_data()
    assign_policy(data, "default", "no_empty_values")
    assign_policy(data, "default", "uppercase_keys")
    result = list_policies_for(data, "default")
    assert "no_empty_values" in result
    assert "uppercase_keys" in result


def test_list_policies_for_empty_vault():
    data = _base_data()
    assert list_policies_for(data, "default") == []


def test_evaluate_policies_pass():
    data = {"DB_HOST": "localhost", "DB_PORT": "5432"}
    assign_policy(data, "default", "uppercase_keys")
    results = evaluate_policies(data, "default")
    assert len(results) == 1
    assert results[0].passed is True
    assert results[0].violations == []


def test_evaluate_policies_fail_on_empty_value():
    data = {"DB_HOST": "", "DB_PORT": "5432"}
    assign_policy(data, "default", "no_empty_values")
    results = evaluate_policies(data, "default")
    assert results[0].passed is False
    assert any("DB_HOST" in v for v in results[0].violations)


def test_evaluate_policies_fail_lowercase_key():
    data = {"db_host": "localhost"}
    assign_policy(data, "myvault", "uppercase_keys")
    results = evaluate_policies(data, "myvault")
    assert results[0].passed is False


def test_evaluate_multiple_policies():
    data = {"db_host": "", "DB_PORT": "5432"}
    assign_policy(data, "default", "uppercase_keys")
    assign_policy(data, "default", "no_empty_values")
    results = evaluate_policies(data, "default")
    assert len(results) == 2
    names = {r.policy for r in results}
    assert "uppercase_keys" in names
    assert "no_empty_values" in names


def test_evaluate_no_policies_returns_empty():
    data = _base_data()
    results = evaluate_policies(data, "default")
    assert results == []


def test_policy_result_repr_pass():
    r = PolicyResult(policy="uppercase_keys", passed=True)
    assert "PASS" in repr(r)


def test_policy_result_repr_fail():
    r = PolicyResult(policy="uppercase_keys", passed=False, violations=["x: bad"])
    assert "FAIL" in repr(r)
