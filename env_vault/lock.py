"""Vault locking: temporarily lock a vault to prevent reads and writes."""

import json
import os
import time
from pathlib import Path

from env_vault.storage import _vault_path


class LockError(Exception):
    """Raised when a lock operation fails."""


def _lock_path(vault_name: str, vault_dir: str | None = None) -> Path:
    base = _vault_path(vault_name, vault_dir).parent
    return base / f"{vault_name}.lock"


def lock_vault(vault_name: str, reason: str = "", vault_dir: str | None = None) -> None:
    """Create a lock file for *vault_name*.

    Raises LockError if the vault is already locked.
    """
    lp = _lock_path(vault_name, vault_dir)
    if lp.exists():
        data = json.loads(lp.read_text())
        raise LockError(
            f"Vault '{vault_name}' is already locked since "
            f"{data.get('locked_at')} — reason: {data.get('reason', 'none')}"
        )
    lp.parent.mkdir(parents=True, exist_ok=True)
    lp.write_text(
        json.dumps({"vault": vault_name, "locked_at": time.time(), "reason": reason})
    )


def unlock_vault(vault_name: str, vault_dir: str | None = None) -> None:
    """Remove the lock file for *vault_name*.

    Raises LockError if the vault is not locked.
    """
    lp = _lock_path(vault_name, vault_dir)
    if not lp.exists():
        raise LockError(f"Vault '{vault_name}' is not locked.")
    lp.unlink()


def is_locked(vault_name: str, vault_dir: str | None = None) -> bool:
    """Return True if *vault_name* has an active lock file."""
    return _lock_path(vault_name, vault_dir).exists()


def get_lock_info(vault_name: str, vault_dir: str | None = None) -> dict | None:
    """Return lock metadata dict, or None if not locked."""
    lp = _lock_path(vault_name, vault_dir)
    if not lp.exists():
        return None
    return json.loads(lp.read_text())


def assert_unlocked(vault_name: str, vault_dir: str | None = None) -> None:
    """Raise LockError if the vault is locked (used as a guard in other modules)."""
    info = get_lock_info(vault_name, vault_dir)
    if info is not None:
        raise LockError(
            f"Vault '{vault_name}' is locked — reason: {info.get('reason', 'none')}"
        )
