"""Freeze and unfreeze vaults — prevent any modifications to vault variables."""

from __future__ import annotations

from typing import Callable

FREEZE_KEY = "__freeze__"


class FreezeError(Exception):
    """Raised when a freeze/unfreeze operation fails."""


def _get_freeze_section(data: dict) -> dict:
    if FREEZE_KEY not in data:
        data[FREEZE_KEY] = {}
    return data[FREEZE_KEY]


def freeze_vault(
    vault_name: str,
    reason: str = "",
    load: Callable = None,
    save: Callable = None,
) -> None:
    """Mark a vault as frozen, optionally recording a reason."""
    from env_vault.storage import load_vault, save_vault

    _load = load or load_vault
    _save = save or save_vault

    data = _load(vault_name)
    if data is None:
        raise FreezeError(f"Vault '{vault_name}' does not exist.")

    section = _get_freeze_section(data)
    if section.get("frozen"):
        raise FreezeError(f"Vault '{vault_name}' is already frozen.")

    section["frozen"] = True
    section["reason"] = reason
    _save(vault_name, data)


def unfreeze_vault(
    vault_name: str,
    load: Callable = None,
    save: Callable = None,
) -> None:
    """Remove the frozen flag from a vault."""
    from env_vault.storage import load_vault, save_vault

    _load = load or load_vault
    _save = save or save_vault

    data = _load(vault_name)
    if data is None:
        raise FreezeError(f"Vault '{vault_name}' does not exist.")

    section = _get_freeze_section(data)
    if not section.get("frozen"):
        raise FreezeError(f"Vault '{vault_name}' is not frozen.")

    section["frozen"] = False
    section["reason"] = ""
    _save(vault_name, data)


def is_frozen(vault_name: str, load: Callable = None) -> bool:
    """Return True if the vault is currently frozen."""
    from env_vault.storage import load_vault

    _load = load or load_vault
    data = _load(vault_name)
    if data is None:
        return False
    return bool(data.get(FREEZE_KEY, {}).get("frozen", False))


def get_freeze_reason(vault_name: str, load: Callable = None) -> str:
    """Return the reason the vault was frozen, or empty string."""
    from env_vault.storage import load_vault

    _load = load or load_vault
    data = _load(vault_name)
    if data is None:
        return ""
    return data.get(FREEZE_KEY, {}).get("reason", "")
