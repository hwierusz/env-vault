"""Copy variables between vaults."""

from typing import Optional
from env_vault.storage import load_vault, save_vault, vault_exists
from env_vault.audit import record_event


class CopyError(Exception):
    """Raised when a copy operation fails."""


def copy_vars(
    src_vault: str,
    dst_vault: str,
    src_password: str,
    dst_password: str,
    keys: Optional[list] = None,
    overwrite: bool = False,
) -> int:
    """Copy variables from one vault to another.

    Args:
        src_vault: Name of the source vault.
        dst_vault: Name of the destination vault.
        src_password: Password for the source vault.
        dst_password: Password for the destination vault.
        keys: Optional list of keys to copy. If None, all keys are copied.
        overwrite: If False, raise CopyError on key conflicts.

    Returns:
        Number of variables copied.

    Raises:
        CopyError: If a vault is missing or a key conflict occurs.
    """
    if not vault_exists(src_vault):
        raise CopyError(f"Source vault '{src_vault}' does not exist.")
    if not vault_exists(dst_vault):
        raise CopyError(f"Destination vault '{dst_vault}' does not exist.")

    src_data = load_vault(src_vault, src_password)
    dst_data = load_vault(dst_vault, dst_password)

    to_copy = {k: v for k, v in src_data.items() if keys is None or k in keys}

    if not overwrite:
        conflicts = [k for k in to_copy if k in dst_data]
        if conflicts:
            raise CopyError(
                f"Key conflict in destination vault: {', '.join(conflicts)}. "
                "Use overwrite=True to replace existing keys."
            )

    dst_data.update(to_copy)
    save_vault(dst_vault, dst_password, dst_data)

    for key in to_copy:
        record_event(dst_vault, "copy", key)

    return len(to_copy)
