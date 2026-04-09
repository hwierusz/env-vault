"""Password rotation for env-vault: re-encrypts vault contents with a new password."""

from typing import Optional
from env_vault.storage import load_vault, save_vault, vault_exists
from env_vault.audit import record_event


class RotationError(Exception):
    """Raised when password rotation fails."""
    pass


def rotate_password(
    vault_name: str,
    old_password: str,
    new_password: str,
    vault_dir: Optional[str] = None,
) -> int:
    """Re-encrypt a vault with a new password.

    Loads the vault using the old password, then saves it back using the new
    password.  Returns the number of variables that were re-encrypted.

    Raises:
        RotationError: if the vault does not exist or the old password is wrong.
    """
    kwargs = {"vault_dir": vault_dir} if vault_dir is not None else {}

    if not vault_exists(vault_name, **kwargs):
        raise RotationError(f"Vault '{vault_name}' does not exist.")

    try:
        data = load_vault(vault_name, old_password, **kwargs)
    except Exception as exc:
        raise RotationError(
            f"Failed to load vault '{vault_name}' with the provided old password."
        ) from exc

    try:
        save_vault(vault_name, data, new_password, **kwargs)
    except Exception as exc:
        raise RotationError(
            f"Failed to save vault '{vault_name}' with the new password."
        ) from exc

    record_event(
        vault_name,
        action="rotate_password",
        key=None,
        vault_dir=vault_dir,
    )

    return len(data)
