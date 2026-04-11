"""PIN-based quick-access lock for vault entries.

Allows setting a short numeric PIN on a specific key so it requires
an additional PIN confirmation before the value is revealed.
"""

from __future__ import annotations

import hashlib
import json
from typing import Callable

PIN_STORE_KEY = "__pins__"


class PinError(Exception):
    pass


def _get_pins(data: dict) -> dict:
    return data.get(PIN_STORE_KEY, {})


def set_pin(
    vault_name: str,
    key: str,
    pin: str,
    load_vault: Callable,
    save_vault: Callable,
) -> None:
    """Attach a PIN hash to *key* inside *vault_name*."""
    if not pin.isdigit():
        raise PinError("PIN must contain digits only.")
    if len(pin) < 4:
        raise PinError("PIN must be at least 4 digits.")

    data = load_vault(vault_name)
    if key not in data:
        raise PinError(f"Key '{key}' not found in vault '{vault_name}'.")

    pins = _get_pins(data)
    pins[key] = hashlib.sha256(pin.encode()).hexdigest()
    data[PIN_STORE_KEY] = pins
    save_vault(vault_name, data)


def remove_pin(
    vault_name: str,
    key: str,
    load_vault: Callable,
    save_vault: Callable,
) -> None:
    """Remove the PIN from *key* if one exists."""
    data = load_vault(vault_name)
    pins = _get_pins(data)
    if key not in pins:
        raise PinError(f"No PIN set for key '{key}'.")
    del pins[key]
    data[PIN_STORE_KEY] = pins
    save_vault(vault_name, data)


def verify_pin(
    vault_name: str,
    key: str,
    pin: str,
    load_vault: Callable,
) -> bool:
    """Return True if *pin* matches the stored PIN for *key*."""
    data = load_vault(vault_name)
    pins = _get_pins(data)
    if key not in pins:
        return True  # no PIN set — access is unrestricted
    return pins[key] == hashlib.sha256(pin.encode()).hexdigest()


def list_pinned_keys(
    vault_name: str,
    load_vault: Callable,
) -> list[str]:
    """Return list of keys that have a PIN attached."""
    data = load_vault(vault_name)
    return list(_get_pins(data).keys())
