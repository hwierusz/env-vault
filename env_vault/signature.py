"""Vault signature — sign and verify vault contents with an HMAC."""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any


class SignatureError(Exception):
    """Raised when a signature operation fails."""


def _stable_serialize(data: dict[str, Any]) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode()


def sign_vault(vars: dict[str, str], secret: str) -> str:
    """Return a hex HMAC-SHA256 signature for *vars* using *secret*."""
    if not secret:
        raise SignatureError("secret must not be empty")
    payload = _stable_serialize(vars)
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def verify_signature(vars: dict[str, str], secret: str, signature: str) -> bool:
    """Return True if *signature* matches the expected signature for *vars*."""
    if not secret:
        raise SignatureError("secret must not be empty")
    expected = sign_vault(vars, secret)
    return hmac.compare_digest(expected, signature)


def attach_signature(data: dict[str, Any], secret: str) -> dict[str, Any]:
    """Return a copy of *data* with a '__signature__' metadata entry."""
    vars: dict[str, str] = data.get("vars", {})
    sig = sign_vault(vars, secret)
    updated = dict(data)
    meta = dict(updated.get("__meta__", {}))
    meta["signature"] = sig
    updated["__meta__"] = meta
    return updated


def check_signature(data: dict[str, Any], secret: str) -> bool:
    """Return True if the stored signature in *data* is valid."""
    sig = data.get("__meta__", {}).get("signature")
    if not sig:
        raise SignatureError("no signature found in vault metadata")
    vars: dict[str, str] = data.get("vars", {})
    return verify_signature(vars, secret, sig)
