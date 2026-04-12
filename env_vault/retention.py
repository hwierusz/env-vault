"""Retention policy management for env-vault variables."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional

RETENTION_KEY = "__retention__"

VALID_UNITS = {"days", "weeks", "months"}


class RetentionError(Exception):
    pass


def _get_retention(data: dict) -> dict:
    return data.setdefault(RETENTION_KEY, {})


def set_retention(
    vault_name: str,
    key: str,
    duration: int,
    unit: str,
    load_fn: Callable,
    save_fn: Callable,
) -> datetime:
    """Set a retention policy for *key*. Returns the computed expiry datetime."""
    if unit not in VALID_UNITS:
        raise RetentionError(
            f"Invalid unit '{unit}'. Choose from: {', '.join(sorted(VALID_UNITS))}"
        )
    if duration <= 0:
        raise RetentionError("Duration must be a positive integer.")

    data = load_fn(vault_name)
    if key not in data.get("vars", {}):
        raise RetentionError(f"Key '{key}' not found in vault '{vault_name}'.")

    if unit == "months":
        delta = timedelta(days=duration * 30)
    elif unit == "weeks":
        delta = timedelta(weeks=duration)
    else:
        delta = timedelta(days=duration)

    expiry = datetime.utcnow() + delta
    retention = _get_retention(data)
    retention[key] = {"duration": duration, "unit": unit, "expires_at": expiry.isoformat()}
    save_fn(vault_name, data)
    return expiry


def get_retention(vault_name: str, key: str, load_fn: Callable) -> Optional[dict]:
    """Return retention info for *key*, or None if not set."""
    data = load_fn(vault_name)
    return _get_retention(data).get(key)


def remove_retention(vault_name: str, key: str, load_fn: Callable, save_fn: Callable) -> bool:
    """Remove retention policy for *key*. Returns True if it existed."""
    data = load_fn(vault_name)
    retention = _get_retention(data)
    if key not in retention:
        return False
    del retention[key]
    save_fn(vault_name, data)
    return True


def list_retention(vault_name: str, load_fn: Callable) -> List[dict]:
    """Return all retention entries as a list of dicts including the key name."""
    data = load_fn(vault_name)
    retention = _get_retention(data)
    result = []
    for k, v in retention.items():
        entry = dict(v)
        entry["key"] = k
        entry["expired"] = datetime.utcnow().isoformat() >= v["expires_at"]
        result.append(entry)
    return result
