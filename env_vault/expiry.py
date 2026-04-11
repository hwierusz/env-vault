"""Bulk expiry reporting and enforcement for env-vault."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from env_vault.ttl import get_ttl, is_expired, TTLError


class ExpiryError(Exception):
    """Raised when an expiry operation fails."""


@dataclass
class ExpiryReport:
    vault_name: str
    expired: List[str] = field(default_factory=list)
    expiring_soon: List[str] = field(default_factory=list)  # within warning_seconds
    healthy: List[str] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.expired or self.expiring_soon)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ExpiryReport(vault={self.vault_name!r}, "
            f"expired={len(self.expired)}, "
            f"expiring_soon={len(self.expiring_soon)}, "
            f"healthy={len(self.healthy)})"
        )


def expiry_report(
    vault_name: str,
    load_fn: Callable[[str, str], Dict[str, str]],
    password: str,
    *,
    warning_seconds: int = 86_400,
) -> ExpiryReport:
    """Produce an ExpiryReport for all keys in *vault_name*.

    Args:
        vault_name: Name of the vault to inspect.
        load_fn: Callable matching ``load_vault(name, password) -> dict``.
        password: Decryption password.
        warning_seconds: Keys expiring within this many seconds are flagged as
            *expiring_soon* rather than healthy. Default is 24 hours.
    """
    try:
        data = load_fn(vault_name, password)
    except Exception as exc:
        raise ExpiryError(f"Could not load vault '{vault_name}': {exc}") from exc

    report = ExpiryReport(vault_name=vault_name)
    now = time.time()

    for key in data.get("vars", {}):
        try:
            expiry: Optional[float] = get_ttl(data, key)
        except TTLError:
            expiry = None

        if expiry is None:
            report.healthy.append(key)
        elif expiry <= now:
            report.expired.append(key)
        elif expiry - now <= warning_seconds:
            report.expiring_soon.append(key)
        else:
            report.healthy.append(key)

    return report


def purge_expired(
    vault_name: str,
    load_fn: Callable[[str, str], Dict[str, str]],
    save_fn: Callable[[str, str, Dict], None],
    password: str,
) -> List[str]:
    """Delete all expired keys from *vault_name* and return their names."""
    try:
        data = load_fn(vault_name, password)
    except Exception as exc:
        raise ExpiryError(f"Could not load vault '{vault_name}': {exc}") from exc

    removed: List[str] = []
    for key in list(data.get("vars", {})):
        try:
            if is_expired(data, key):
                del data["vars"][key]
                removed.append(key)
        except TTLError:
            pass

    if removed:
        try:
            save_fn(vault_name, password, data)
        except Exception as exc:
            raise ExpiryError(f"Could not save vault '{vault_name}': {exc}") from exc

    return removed
