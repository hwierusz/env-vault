"""Tests for env_vault.compare."""

import pytest

from env_vault.compare import CompareError, CompareResult, compare_vaults


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_loader(mapping: dict):
    """Return a fake loader that serves pre-built vault data."""
    def _loader(name: str, password: str) -> dict:
        if name not in mapping:
            raise KeyError(f"vault '{name}' not found")
        return {"vars": mapping[name]}
    return _loader


VAULT_A = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "abc"}
VAULT_B = {"DB_HOST": "remotehost", "DB_PORT": "5432", "API_KEY": "xyz"}


@pytest.fixture()
def result() -> CompareResult:
    loader = _make_loader({"a": VAULT_A, "b": VAULT_B})
    return compare_vaults("a", "pw", "b", "pw", loader=loader)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_only_in_a(result):
    assert result.only_in_a == ["SECRET"]


def test_only_in_b(result):
    assert result.only_in_b == ["API_KEY"]


def test_changed_keys(result):
    keys = [entry[0] for entry in result.changed]
    assert keys == ["DB_HOST"]


def test_changed_values(result):
    _, val_a, val_b = result.changed[0]
    assert val_a == "localhost"
    assert val_b == "remotehost"


def test_identical_keys(result):
    assert result.identical == ["DB_PORT"]


def test_has_differences_true(result):
    assert result.has_differences is True


def test_has_differences_false():
    same = {"KEY": "value"}
    loader = _make_loader({"x": same, "y": same})
    r = compare_vaults("x", "pw", "y", "pw", loader=loader)
    assert r.has_differences is False


def test_summary_contains_vault_names(result):
    summary = result.summary()
    assert "'a'" in summary
    assert "'b'" in summary


def test_summary_counts(result):
    summary = result.summary()
    assert "Only in a: 1" in summary
    assert "Only in b: 1" in summary
    assert "Changed: 1" in summary
    assert "Identical: 1" in summary


def test_compare_error_on_missing_vault_a():
    loader = _make_loader({"b": VAULT_B})
    with pytest.raises(CompareError, match="vault 'a'"):
        compare_vaults("a", "pw", "b", "pw", loader=loader)


def test_compare_error_on_missing_vault_b():
    loader = _make_loader({"a": VAULT_A})
    with pytest.raises(CompareError, match="vault 'b'"):
        compare_vaults("a", "pw", "b", "pw", loader=loader)


def test_vault_names_stored_on_result():
    loader = _make_loader({"prod": {}, "staging": {}})
    r = compare_vaults("prod", "pw", "staging", "pw", loader=loader)
    assert r.vault_a == "prod"
    assert r.vault_b == "staging"
