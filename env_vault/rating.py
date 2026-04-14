"""Vault rating module — assigns a letter grade based on score and lint findings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from env_vault.score import score_vault, ScoreError
from env_vault.lint import lint_vars, LintWarning


class RatingError(Exception):
    """Raised when rating cannot be computed."""


# Grade thresholds (inclusive lower bound)
_THRESHOLDS = [
    (90, "A"),
    (75, "B"),
    (60, "C"),
    (40, "D"),
    (0,  "F"),
]


@dataclass
class RatingResult:
    grade: str
    score: int
    findings: int
    summary: str

    def __repr__(self) -> str:  # pragma: no cover
        return f"RatingResult(grade={self.grade!r}, score={self.score}, findings={self.findings})"


def _grade(score: int) -> str:
    for threshold, letter in _THRESHOLDS:
        if score >= threshold:
            return letter
    return "F"


def rate_vault(
    vault_name: str,
    password: str,
    load_fn=None,
    get_ttl_fn=None,
) -> RatingResult:
    """Compute a letter-grade rating for a vault.

    Parameters
    ----------
    vault_name:  name of the vault to rate.
    password:    decryption password.
    load_fn:     optional override for loading vault data (testing).
    get_ttl_fn:  optional override for TTL lookup (testing).
    """
    try:
        kwargs: dict = {"vault_name": vault_name, "password": password}
        if load_fn is not None:
            kwargs["load_fn"] = load_fn
        if get_ttl_fn is not None:
            kwargs["get_ttl_fn"] = get_ttl_fn
        report = score_vault(**kwargs)
    except ScoreError as exc:
        raise RatingError(str(exc)) from exc

    vars_data = report.vars if hasattr(report, "vars") else {}
    findings: List[LintWarning] = []
    if vars_data:
        findings = lint_vars(vars_data)

    # Penalise score by 2 points per lint finding (capped at 20)
    penalty = min(len(findings) * 2, 20)
    adjusted = max(0, report.score - penalty)

    grade = _grade(adjusted)
    summary = (
        f"Score {adjusted}/100 (raw {report.score}, -{penalty} for {len(findings)} lint issue(s))"
    )
    return RatingResult(
        grade=grade,
        score=adjusted,
        findings=len(findings),
        summary=summary,
    )
