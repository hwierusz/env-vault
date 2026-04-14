"""Tests for env_vault.rating."""

from __future__ import annotations

import pytest

from env_vault.rating import rate_vault, RatingError, _grade
from env_vault.score import ScoreReport


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_report(score: int, vars_data: dict | None = None):
    """Return a minimal ScoreReport-like object."""
    report = ScoreReport(
        vault_name="test",
        score=score,
        total_vars=len(vars_data or {}),
        issues=[],
    )
    # Attach vars so lint can inspect them
    report.vars = vars_data or {}
    return report


def _make_rate(score: int, vars_data: dict | None = None):
    """Convenience wrapper around rate_vault with mocked internals."""
    report = _make_report(score, vars_data)

    def _fake_score(vault_name, password, **_kwargs):
        return report

    import env_vault.rating as mod
    original = mod.score_vault
    mod.score_vault = _fake_score
    try:
        result = rate_vault("test", "pass")
    finally:
        mod.score_vault = original
    return result


# ---------------------------------------------------------------------------
# _grade
# ---------------------------------------------------------------------------

def test_grade_a():
    assert _grade(95) == "A"

def test_grade_a_boundary():
    assert _grade(90) == "A"

def test_grade_b():
    assert _grade(80) == "B"

def test_grade_c():
    assert _grade(65) == "C"

def test_grade_d():
    assert _grade(50) == "D"

def test_grade_f():
    assert _grade(30) == "F"

def test_grade_zero():
    assert _grade(0) == "F"


# ---------------------------------------------------------------------------
# rate_vault
# ---------------------------------------------------------------------------

def test_rate_vault_returns_rating_result():
    result = _make_rate(100)
    assert result.grade == "A"
    assert result.score == 100
    assert result.findings == 0


def test_rate_vault_lint_penalty_applied():
    # Vars with lowercase keys will trigger lint findings
    vars_data = {"lowercase_key": "value", "another_bad": "val"}
    result = _make_rate(100, vars_data)
    assert result.score < 100
    assert result.findings >= 2


def test_rate_vault_penalty_capped_at_20():
    # Many bad keys should not push score below 0
    vars_data = {f"bad_key_{i}": "v" for i in range(20)}
    result = _make_rate(10, vars_data)
    assert result.score >= 0


def test_rate_vault_raises_on_score_error():
    import env_vault.rating as mod
    from env_vault.score import ScoreError

    original = mod.score_vault
    mod.score_vault = lambda *a, **kw: (_ for _ in ()).throw(ScoreError("boom"))
    try:
        with pytest.raises(RatingError, match="boom"):
            rate_vault("missing", "pass")
    finally:
        mod.score_vault = original


def test_rate_vault_summary_contains_score():
    result = _make_rate(85)
    assert "85" in result.summary
