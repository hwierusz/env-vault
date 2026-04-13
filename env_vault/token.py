"""Token-based access management for vault variables."""
from __future__ import annotations

import secrets
import time
from typing import Any


class TokenError(Exception):
    pass


_TOKENS_KEY = "__tokens__"


def _get_tokens(data: dict) -> dict:
    return data.setdefault(_TOKENS_KEY, {})


def issue_token(
    data: dict,
    label: str,
    allowed_keys: list[str],
    ttl_seconds: int = 3600,
) -> str:
    """Issue a new access token granting read access to allowed_keys."""
    if not allowed_keys:
        raise TokenError("allowed_keys must not be empty")
    if ttl_seconds <= 0:
        raise TokenError("ttl_seconds must be positive")
    vars_section = {k: v for k, v in data.items() if not k.startswith("__")}
    for key in allowed_keys:
        if key not in vars_section:
            raise TokenError(f"Key not found in vault: {key}")
    token = secrets.token_hex(32)
    _get_tokens(data)[token] = {
        "label": label,
        "allowed_keys": list(allowed_keys),
        "issued_at": time.time(),
        "expires_at": time.time() + ttl_seconds,
    }
    return token


def revoke_token(data: dict, token: str) -> None:
    """Revoke an existing token."""
    tokens = _get_tokens(data)
    if token not in tokens:
        raise TokenError("Token not found")
    del tokens[token]


def resolve_token(data: dict, token: str) -> dict[str, Any]:
    """Resolve a token to its allowed key/value pairs, raising if expired."""
    tokens = _get_tokens(data)
    if token not in tokens:
        raise TokenError("Token not found")
    entry = tokens[token]
    if time.time() > entry["expires_at"]:
        raise TokenError("Token has expired")
    return {k: data[k] for k in entry["allowed_keys"] if k in data}


def list_tokens(data: dict) -> list[dict[str, Any]]:
    """Return metadata for all tokens (without the token values themselves)."""
    now = time.time()
    result = []
    for token, entry in _get_tokens(data).items():
        result.append({
            "token": token[:8] + "...",
            "label": entry["label"],
            "allowed_keys": entry["allowed_keys"],
            "expires_at": entry["expires_at"],
            "expired": now > entry["expires_at"],
        })
    return result


def purge_expired_tokens(data: dict) -> int:
    """Remove all expired tokens. Returns count of removed tokens."""
    now = time.time()
    tokens = _get_tokens(data)
    expired = [t for t, e in tokens.items() if now > e["expires_at"]]
    for t in expired:
        del tokens[t]
    return len(expired)
