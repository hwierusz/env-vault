"""Backup and restore vault data to/from an encrypted archive file."""

import json
import os
from datetime import datetime, timezone

from env_vault.crypto import encrypt, decrypt
from env_vault.storage import load_vault, save_vault, vault_exists


class BackupError(Exception):
    pass


def create_backup(vault_name: str, password: str, dest_path: str) -> str:
    """Encrypt and write vault contents to *dest_path*.

    Returns the absolute path of the written backup file.
    """
    if not vault_exists(vault_name):
        raise BackupError(f"Vault '{vault_name}' does not exist.")

    data = load_vault(vault_name, password)
    payload = json.dumps(
        {
            "vault": vault_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "vars": data,
        }
    ).encode()

    ciphertext = encrypt(payload, password)
    dest_path = os.path.abspath(dest_path)
    with open(dest_path, "wb") as fh:
        fh.write(ciphertext)
    return dest_path


def restore_backup(src_path: str, password: str, vault_name: str | None = None) -> str:
    """Decrypt *src_path* and write variables into the target vault.

    If *vault_name* is None the original vault name stored in the backup is used.
    Returns the vault name that was restored into.
    """
    src_path = os.path.abspath(src_path)
    if not os.path.isfile(src_path):
        raise BackupError(f"Backup file not found: {src_path}")

    with open(src_path, "rb") as fh:
        ciphertext = fh.read()

    try:
        plaintext = decrypt(ciphertext, password)
    except Exception as exc:
        raise BackupError("Failed to decrypt backup — wrong password?") from exc

    try:
        payload = json.loads(plaintext.decode())
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise BackupError("Backup payload is corrupt.") from exc

    target = vault_name or payload.get("vault")
    if not target:
        raise BackupError("Cannot determine target vault name.")

    save_vault(target, password, payload["vars"])
    return target
