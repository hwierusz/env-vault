"""Forecast expiry and TTL events for vault variables."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from env_vault.ttl import get_ttl


class ForecastError(Exception):
    """Raised when forecasting fails."""


@dataclass
class ForecastEntry:
    key: str
    expires_at: datetime
    seconds_remaining: float
    status: str  # 'ok', 'warning', 'expired'

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ForecastEntry(key={self.key!r}, status={self.status!r}, "
            f"seconds_remaining={self.seconds_remaining:.0f})"
        )


def _classify(seconds_remaining: float, warning_threshold: int) -> str:
    if seconds_remaining <= 0:
        return "expired"
    if seconds_remaining <= warning_threshold:
        return "warning"
    return "ok"


def forecast_vault(
    vault_name: str,
    password: str,
    *,
    warning_threshold: int = 86400,
    load_fn: Optional[Callable] = None,
    ttl_fn: Optional[Callable] = None,
    now: Optional[datetime] = None,
) -> List[ForecastEntry]:
    """Return forecast entries for all keys that have a TTL set.

    Args:
        vault_name: Name of the vault to inspect.
        password: Vault decryption password.
        warning_threshold: Seconds before expiry to flag as 'warning'.
        load_fn: Optional override for load_vault (for testing).
        ttl_fn: Optional override for get_ttl (for testing).
        now: Optional current time override (for testing).
    """
    if load_fn is None:
        from env_vault.storage import load_vault
        load_fn = load_vault

    if ttl_fn is None:
        ttl_fn = get_ttl

    if now is None:
        now = datetime.now(timezone.utc)

    try:
        data: Dict = load_fn(vault_name, password)
    except Exception as exc:
        raise ForecastError(f"Could not load vault '{vault_name}': {exc}") from exc

    vars_section: Dict[str, str] = data.get("vars", {})
    entries: List[ForecastEntry] = []

    for key in vars_section:
        expiry = ttl_fn(data, key)
        if expiry is None:
            continue
        delta = (expiry - now).total_seconds()
        status = _classify(delta, warning_threshold)
        entries.append(
            ForecastEntry(
                key=key,
                expires_at=expiry,
                seconds_remaining=delta,
                status=status,
            )
        )

    entries.sort(key=lambda e: e.expires_at)
    return entries
