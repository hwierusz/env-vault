"""Vault health scoring — rates a vault on security and hygiene practices."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from env_vault.lint import lint_vars
from env_vault.ttl import get_ttl, is_expired


class ScoreError(Exception):
    """Raised when scoring cannot be completed."""


@dataclass
class ScoreReport:
    vault_name: str
    total_vars: int
    score: int  # 0-100
    deductions: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ScoreReport(vault={self.vault_name!r}, score={self.score}, "
            f"vars={self.total_vars})"
        )


_MAX_VARS_BEFORE_PENALTY = 50
_PENALTY_PER_LINT_FINDING = 3
_PENALTY_NO_TTL = 10
_PENALTY_EXPIRED_KEY = 5
_PENALTY_OVERSIZED = 8


def score_vault(
    vault_name: str,
    vars_data: dict[str, Any],
    load_fn=None,
    save_fn=None,
) -> ScoreReport:
    """Compute a 0-100 health score for *vault_name*.

    Parameters
    ----------
    vault_name:
        Name of the vault being scored (used for TTL look-ups).
    vars_data:
        Mapping of key -> value already decrypted from the vault.
    load_fn / save_fn:
        Optional overrides for storage (used in tests).
    """
    deductions: list[str] = []
    suggestions: list[str] = []
    score = 100
    total = len(vars_data)

    if total == 0:
        return ScoreReport(
            vault_name=vault_name,
            total_vars=0,
            score=100,
            suggestions=["Vault is empty — nothing to score."],
        )

    # --- lint findings ---
    findings = lint_vars(vars_data)
    if findings:
        penalty = min(len(findings) * _PENALTY_PER_LINT_FINDING, 30)
        score -= penalty
        deductions.append(
            f"{len(findings)} lint finding(s) (-{penalty} pts)"
        )
        suggestions.append("Run 'env-vault lint' and fix reported issues.")

    # --- TTL coverage ---
    keys_without_ttl = []
    expired_keys = []
    for key in vars_data:
        ttl_val = get_ttl(vault_name, key, load_fn=load_fn)
        if ttl_val is None:
            keys_without_ttl.append(key)
        elif is_expired(vault_name, key, load_fn=load_fn):
            expired_keys.append(key)

    if keys_without_ttl:
        ratio = len(keys_without_ttl) / total
        penalty = int(ratio * _PENALTY_NO_TTL)
        score -= penalty
        deductions.append(
            f"{len(keys_without_ttl)} key(s) have no TTL (-{penalty} pts)"
        )
        suggestions.append("Set TTLs on sensitive keys with 'env-vault ttl set'.")

    if expired_keys:
        penalty = min(len(expired_keys) * _PENALTY_EXPIRED_KEY, 20)
        score -= penalty
        deductions.append(
            f"{len(expired_keys)} expired key(s) still present (-{penalty} pts)"
        )
        suggestions.append("Remove or renew expired keys with 'env-vault ttl purge'.")

    # --- vault size ---
    if total > _MAX_VARS_BEFORE_PENALTY:
        score -= _PENALTY_OVERSIZED
        deductions.append(
            f"Vault has {total} variables (>{_MAX_VARS_BEFORE_PENALTY}) (-{_PENALTY_OVERSIZED} pts)"
        )
        suggestions.append("Consider splitting large vaults into namespaces or profiles.")

    score = max(score, 0)
    return ScoreReport(
        vault_name=vault_name,
        total_vars=total,
        score=score,
        deductions=deductions,
        suggestions=suggestions,
    )
