"""Merge variables from one vault into another."""

from typing import Optional
from env_vault.storage import load_vault, save_vault, vault_exists
from env_vault.audit import record_event


class MergeError(Exception):
    """Raised when a merge operation fails."""


def merge_vaults(
    src_name: str,
    src_password: str,
    dst_name: str,
    dst_password: str,
    overwrite: bool = False,
    keys: Optional[list] = None,
) -> dict:
    """Merge variables from src vault into dst vault.

    Args:
        src_name: Name of the source vault.
        src_password: Password for the source vault.
        dst_name: Name of the destination vault.
        dst_password: Password for the destination vault.
        overwrite: If True, overwrite existing keys in dst. Default False.
        keys: Optional list of specific keys to merge. Merges all if None.

    Returns:
        A dict with 'added' and 'skipped' lists of key names.

    Raises:
        MergeError: If either vault does not exist or passwords are wrong.
    """
    if not vault_exists(src_name):
        raise MergeError(f"Source vault '{src_name}' does not exist.")
    if not vault_exists(dst_name):
        raise MergeError(f"Destination vault '{dst_name}' does not exist.")

    try:
        src_data = load_vault(src_name, src_password)
    except Exception as exc:
        raise MergeError(f"Failed to load source vault '{src_name}': {exc}") from exc

    try:
        dst_data = load_vault(dst_name, dst_password)
    except Exception as exc:
        raise MergeError(f"Failed to load destination vault '{dst_name}': {exc}") from exc

    candidates = {k: v for k, v in src_data.items() if keys is None or k in keys}

    added = []
    skipped = []

    for key, value in candidates.items():
        if key in dst_data and not overwrite:
            skipped.append(key)
        else:
            dst_data[key] = value
            added.append(key)

    save_vault(dst_name, dst_password, dst_data)

    for key in added:
        record_event(dst_name, "merge", key)

    return {"added": added, "skipped": skipped}
