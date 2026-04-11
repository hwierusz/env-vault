"""Quota enforcement for env-vault: limit the number of variables per vault."""

from __future__ import annotations

from typing import Callable

DEFAULT_QUOTA = 100
_QUOTA_KEY = "__quota__"


class QuotaError(Exception):
    """Raised when a quota operation fails."""


def _get_quota_section(data: dict) -> dict:
    return data.setdefault(_QUOTA_KEY, {})


def set_quota(
    vault_name: str,
    limit: int,
    load: Callable,
    save: Callable,
) -> None:
    """Set the maximum number of variables allowed in *vault_name*."""
    if limit < 1:
        raise QuotaError("Quota limit must be a positive integer.")
    data = load(vault_name)
    _get_quota_section(data)["limit"] = limit
    save(vault_name, data)


def get_quota(
    vault_name: str,
    load: Callable,
) -> int:
    """Return the quota limit for *vault_name* (default: DEFAULT_QUOTA)."""
    data = load(vault_name)
    return _get_quota_section(data).get("limit", DEFAULT_QUOTA)


def remove_quota(
    vault_name: str,
    load: Callable,
    save: Callable,
) -> None:
    """Remove any custom quota from *vault_name*, reverting to the default."""
    data = load(vault_name)
    section = _get_quota_section(data)
    section.pop("limit", None)
    save(vault_name, data)


def check_quota(
    vault_name: str,
    load: Callable,
) -> tuple[int, int]:
    """Return (current_count, limit) for *vault_name*."""
    data = load(vault_name)
    limit = _get_quota_section(data).get("limit", DEFAULT_QUOTA)
    current = len([k for k in data if not k.startswith("__")])
    return current, limit


def enforce_quota(
    vault_name: str,
    load: Callable,
) -> None:
    """Raise QuotaError if the vault has reached or exceeded its limit."""
    current, limit = check_quota(vault_name, load)
    if current >= limit:
        raise QuotaError(
            f"Vault '{vault_name}' has reached its quota of {limit} variable(s). "
            f"Current count: {current}."
        )
