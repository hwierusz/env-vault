"""Tests for env_vault.maturity."""
import pytest
from unittest.mock import patch
from env_vault.maturity import (
    assess_maturity,
    MaturityError,
    MaturityReport,
    LEVELS,
    _score_key_hygiene,
    _score_ttl_coverage,
)


def _make_loader(data):
    def _load(vault_name, password):
        return data
    return _load


BASE_VARS = {"DB_HOST": "localhost", "API_KEY": "secret", "PORT": "5432"}


def test_report_level_optimizing():
    r = MaturityReport(vault_name="v", scores={"a": 95, "b": 91, "c": 92})
    assert r.level == "optimizing"


def test_report_level_initial():
    r = MaturityReport(vault_name="v", scores={"a": 10, "b": 20})
    assert r.level == "initial"


def test_report_overall_average():
    r = MaturityReport(vault_name="v", scores={"x": 80, "y": 60})
    assert r.overall == 70


def test_report_overall_empty():
    r = MaturityReport(vault_name="v")
    assert r.overall == 0


def test_repr_contains_vault_name():
    r = MaturityReport(vault_name="myvault", scores={"a": 50})
    assert "myvault" in repr(r)


def test_score_key_hygiene_all_clean():
    assert _score_key_hygiene({"DB_HOST": "x", "API_KEY": "y"}) == 100


def test_score_key_hygiene_mixed():
    score = _score_key_hygiene({"db_host": "x", "API_KEY": "y"})
    assert score == 50


def test_score_key_hygiene_empty():
    assert _score_key_hygiene({}) == 100


def test_assess_maturity_returns_report():
    loader = _make_loader(BASE_VARS)
    with patch("env_vault.maturity.get_ttl", return_value=None), \
         patch("env_vault.maturity.read_events", return_value=[]):
        report = assess_maturity("myvault", "pass", load_fn=loader)
    assert isinstance(report, MaturityReport)
    assert report.vault_name == "myvault"
    assert "key_hygiene" in report.scores


def test_assess_maturity_raises_on_load_error():
    def bad_load(name, pw):
        raise RuntimeError("disk error")
    with pytest.raises(MaturityError, match="disk error"):
        assess_maturity("x", "pw", load_fn=bad_load)


def test_assess_maturity_skips_private_keys():
    data = {"_meta": "ignored", "REAL_KEY": "val"}
    loader = _make_loader(data)
    with patch("env_vault.maturity.get_ttl", return_value=None), \
         patch("env_vault.maturity.read_events", return_value=[]):
        report = assess_maturity("v", "pw", load_fn=loader)
    assert report.scores["key_hygiene"] == 100


def test_levels_list_has_five_entries():
    assert len(LEVELS) == 5
