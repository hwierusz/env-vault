"""Cascade resolution: merge variables from multiple vaults in priority order."""

from typing import List, Dict, Optional
from env_vault.storage import load_vault, vault_exists


class CascadeError(Exception):
    pass


def resolve_cascade(
    vault_names: List[str],
    password: str,
    base_dir: Optional[str] = None,
) -> Dict[str, str]:
    """Resolve variables by merging vaults left-to-right (last wins).

    Args:
        vault_names: Ordered list of vault names; later entries take priority.
        password: Shared decryption password for all vaults.
        base_dir: Optional override for vault storage directory.

    Returns:
        Merged dict of environment variables.

    Raises:
        CascadeError: If any named vault does not exist.
    """
    if not vault_names:
        raise CascadeError("At least one vault name must be provided.")

    kwargs = {"base_dir": base_dir} if base_dir is not None else {}

    for name in vault_names:
        if not vault_exists(name, **kwargs):
            raise CascadeError(f"Vault not found: {name!r}")

    merged: Dict[str, str] = {}
    for name in vault_names:
        data = load_vault(name, password, **kwargs)
        vars_section = data.get("vars", {})
        merged.update(vars_section)

    return merged


def cascade_sources(
    vault_names: List[str],
    password: str,
    base_dir: Optional[str] = None,
) -> Dict[str, str]:
    """Return a mapping of key -> vault_name indicating which vault last defined it."""
    if not vault_names:
        raise CascadeError("At least one vault name must be provided.")

    kwargs = {"base_dir": base_dir} if base_dir is not None else {}

    for name in vault_names:
        if not vault_exists(name, **kwargs):
            raise CascadeError(f"Vault not found: {name!r}")

    sources: Dict[str, str] = {}
    for name in vault_names:
        data = load_vault(name, password, **kwargs)
        for key in data.get("vars", {}):
            sources[key] = name

    return sources
