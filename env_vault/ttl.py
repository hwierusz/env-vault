"""TTL (time-to-live) support for vault variables."""

import time
from typing import Optional

TTL_META_KEY = "__ttl_meta__"


class TTLError(Exception):
    pass


def set_ttl(data: dict, key: str, ttl_seconds: int) -> dict:
    """Record an expiry timestamp for *key* inside the vault data dict."""
    if key not in data:
        raise TTLError(f"Key '{key}' not found in vault.")
    if ttl_seconds <= 0:
        raise TTLError("TTL must be a positive integer.")

    meta = data.get(TTL_META_KEY, {})
    meta[key] = time.time() + ttl_seconds
    data[TTL_META_KEY] = meta
    return data


def get_ttl(data: dict, key: str) -> Optional[float]:
    """Return the UNIX expiry timestamp for *key*, or None if no TTL is set."""
    meta = data.get(TTL_META_KEY, {})
    return meta.get(key)


def remove_ttl(data: dict, key: str) -> dict:
    """Remove the TTL entry for *key* without deleting the variable."""
    meta = data.get(TTL_META_KEY, {})
    meta.pop(key, None)
    if meta:
        data[TTL_META_KEY] = meta
    else:
        data.pop(TTL_META_KEY, None)
    return data


def is_expired(data: dict, key: str) -> bool:
    """Return True if *key* has a TTL that has already passed."""
    expiry = get_ttl(data, key)
    if expiry is None:
        return False
    return time.time() >= expiry


def purge_expired(data: dict) -> list:
    """Delete all variables whose TTL has expired.  Returns list of purged keys."""
    meta = data.get(TTL_META_KEY, {})
    now = time.time()
    expired = [k for k, exp in list(meta.items()) if now >= exp]
    for key in expired:
        data.pop(key, None)
        meta.pop(key, None)
    if meta:
        data[TTL_META_KEY] = meta
    else:
        data.pop(TTL_META_KEY, None)
    return expired
