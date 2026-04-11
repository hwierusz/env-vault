"""Tests for env_vault.score."""
from __future__ import annotations

import pytest

from env_vault.score import ScoreReport, ScoreError, score_vault


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _no_ttl(vault, key, load_fn=None):
    return None


def _ttl_for_all(seconds=3600):
    """Return a get_ttl stub that always returns *seconds*."""
    import time
    expiry = time.time() + seconds

    def _fn(vault, key, load_fn=None):
        return expiry

    return _fn


def _expired_ttl(vault, key, load_fn=None):
    import time
    return time.time() - 1  # already in the past


# ---------------------------------------------------------------------------
# empty vault
# ---------------------------------------------------------------------------

def test_empty_vault_scores_100():
    report = score_vault("demo", {}, load_fn=None)
    assert report.score == 100
    assert report.total_vars == 0


# ---------------------------------------------------------------------------
# clean vault
# ---------------------------------------------------------------------------

def test_clean_vault_with_ttls_scores_100(monkeypatch):
    monkeypatch.setattr("env_vault.score.get_ttl", _ttl_for_all())
    monkeypatch.setattr("env_vault.score.is_expired", lambda v, k, load_fn=None: False)
    vars_data = {"DB_HOST": "localhost", "API_KEY": "secret"}
    report = score_vault("demo", vars_data)
    assert report.score == 100
    assert report.deductions == []


# ---------------------------------------------------------------------------
# lint deductions
# ---------------------------------------------------------------------------

def test_lint_findings_reduce_score(monkeypatch):
    monkeypatch.setattr("env_vault.score.get_ttl", _ttl_for_all())
    monkeypatch.setattr("env_vault.score.is_expired", lambda v, k, load_fn=None: False)
    # lowercase keys will trigger lint warnings
    vars_data = {"bad_key": "value", "another_bad": "v2"}
    report = score_vault("demo", vars_data)
    assert report.score < 100
    assert any("lint" in d for d in report.deductions)


# ---------------------------------------------------------------------------
# TTL deductions
# ---------------------------------------------------------------------------

def test_missing_ttl_reduces_score(monkeypatch):
    monkeypatch.setattr("env_vault.score.get_ttl", _no_ttl)
    monkeypatch.setattr("env_vault.score.is_expired", lambda v, k, load_fn=None: False)
    vars_data = {"DB_HOST": "localhost", "API_KEY": "secret"}
    report = score_vault("demo", vars_data)
    assert report.score < 100
    assert any("no TTL" in d for d in report.deductions)


def test_expired_keys_reduce_score(monkeypatch):
    monkeypatch.setattr("env_vault.score.get_ttl", _expired_ttl)
    monkeypatch.setattr("env_vault.score.is_expired", lambda v, k, load_fn=None: True)
    vars_data = {"DB_HOST": "localhost"}
    report = score_vault("demo", vars_data)
    assert report.score < 100
    assert any("expired" in d for d in report.deductions)


# ---------------------------------------------------------------------------
# oversized vault
# ---------------------------------------------------------------------------

def test_oversized_vault_penalised(monkeypatch):
    monkeypatch.setattr("env_vault.score.get_ttl", _ttl_for_all())
    monkeypatch.setattr("env_vault.score.is_expired", lambda v, k, load_fn=None: False)
    # 51 clean keys
    vars_data = {f"KEY_{i}": str(i) for i in range(51)}
    report = score_vault("demo", vars_data)
    assert report.score < 100
    assert any("variables" in d for d in report.deductions)


# ---------------------------------------------------------------------------
# score never goes below zero
# ---------------------------------------------------------------------------

def test_score_floor_is_zero(monkeypatch):
    monkeypatch.setattr("env_vault.score.get_ttl", _expired_ttl)
    monkeypatch.setattr("env_vault.score.is_expired", lambda v, k, load_fn=None: True)
    # many bad keys to pile up penalties
    vars_data = {f"bad_key_{i}": str(i) for i in range(60)}
    report = score_vault("demo", vars_data)
    assert report.score >= 0


# ---------------------------------------------------------------------------
# ScoreReport repr smoke test
# ---------------------------------------------------------------------------

def test_score_report_fields():
    r = ScoreReport(vault_name="x", total_vars=3, score=75,
                    deductions=["d1"], suggestions=["s1"])
    assert r.vault_name == "x"
    assert r.total_vars == 3
    assert r.score == 75
    assert r.deductions == ["d1"]
    assert r.suggestions == ["s1"]
