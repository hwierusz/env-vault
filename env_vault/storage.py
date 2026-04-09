"""Persistent storage layer for encrypted vault files."""

import json
import os
from pathlib import Path

from env_vault.crypto import encrypt, decrypt

DEFAULT_VAULT_DIR = Path.home() / ".env-vault"


def _vault_path(project: str, vault_dir: Path = DEFAULT_VAULT_DIR) -> Path:
    """Return the file path for a project's vault."""
    return vault_dir / f"{project}.vault"


def save_vault(project: str, variables: dict[str, str], password: str,
               vault_dir: Path = DEFAULT_VAULT_DIR) -> Path:
    """Encrypt and persist environment variables for a project."""
    vault_dir.mkdir(parents=True, exist_ok=True)
    plaintext = json.dumps(variables)
    encrypted = encrypt(plaintext, password)
    path = _vault_path(project, vault_dir)
    path.write_bytes(encrypted)
    return path


def load_vault(project: str, password: str,
               vault_dir: Path = DEFAULT_VAULT_DIR) -> dict[str, str]:
    """Load and decrypt environment variables for a project.

    Raises FileNotFoundError if the vault does not exist.
    Raises ValueError on decryption failure.
    """
    path = _vault_path(project, vault_dir)
    if not path.exists():
        raise FileNotFoundError(f"No vault found for project '{project}'.")
    encrypted = path.read_bytes()
    plaintext = decrypt(encrypted, password)
    return json.loads(plaintext)


def vault_exists(project: str, vault_dir: Path = DEFAULT_VAULT_DIR) -> bool:
    """Return True if a vault file exists for the given project."""
    return _vault_path(project, vault_dir).exists()


def list_vaults(vault_dir: Path = DEFAULT_VAULT_DIR) -> list[str]:
    """Return a list of project names that have stored vaults."""
    if not vault_dir.exists():
        return []
    return [p.stem for p in sorted(vault_dir.glob("*.vault"))]


def delete_vault(project: str, vault_dir: Path = DEFAULT_VAULT_DIR) -> bool:
    """Delete the vault for a project. Returns True if deleted, False if not found."""
    path = _vault_path(project, vault_dir)
    if path.exists():
        path.unlink()
        return True
    return False
