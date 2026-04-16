"""Vault maturity assessment — scores a vault across multiple dimensions."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable

from env_vault.storage import load_vault
from env_vault.ttl import get_ttl
from env_vault.audit import read_events


class MaturityError(Exception):
    pass


LEVELS = ["initial", "developing", "defined", "managed", "optimizing"]


@dataclass
class MaturityReport:
    vault_name: str
    scores: dict[str, int] = field(default_factory=dict)

    @property
    def overall(self) -> int:
        if not self.scores:
            return 0
        return round(sum(self.scores.values()) / len(self.scores))

    @property
    def level(self) -> str:
        o = self.overall
        if o >= 90:
            return LEVELS[4]
        if o >= 75:
            return LEVELS[3]
        if o >= 55:
            return LEVELS[2]
        if o >= 35:
            return LEVELS[1]
        return LEVELS[0]

    def __repr__(self) -> str:
        return f"<MaturityReport vault={self.vault_name!r} overall={self.overall} level={self.level!r}>"


def _score_ttl_coverage(vars_: dict, password: str, vault_name: str) -> int:
    if not vars_:
        return 100
    covered = sum(1 for k in vars_ if get_ttl(vault_name, k, password) is not None)
    return round(covered / len(vars_) * 100)


def _score_audit_activity(vault_name: str) -> int:
    try:
        events = read_events(vault_name)
    except Exception:
        return 0
    return min(100, len(events) * 5)


def _score_key_hygiene(vars_: dict) -> int:
    if not vars_:
        return 100
    clean = sum(1 for k in vars_ if k == k.upper() and k.replace("_", "").isalnum())
    return round(clean / len(vars_) * 100)


def assess_maturity(vault_name: str, password: str,
                    load_fn: Callable = load_vault) -> MaturityReport:
    try:
        data = load_fn(vault_name, password)
    except Exception as exc:
        raise MaturityError(f"Cannot load vault '{vault_name}': {exc}") from exc

    vars_ = {k: v for k, v in data.items() if not k.startswith("_")}
    report = MaturityReport(vault_name=vault_name)
    report.scores["ttl_coverage"] = _score_ttl_coverage(vars_, password, vault_name)
    report.scores["audit_activity"] = _score_audit_activity(vault_name)
    report.scores["key_hygiene"] = _score_key_hygiene(vars_)
    return report
