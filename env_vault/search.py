"""Search and filter environment variables across vaults."""

import json
import re
from typing import Optional

from env_vault.storage import load_vault
from env_vault.crypto import decrypt


class SearchError(Exception):
    pass


def search_vars(
    vault_name: str,
    password: str,
    pattern: str,
    search_values: bool = False,
    case_sensitive: bool = False,
) -> dict:
    """Search for variables in a vault by key (and optionally value) pattern.

    Args:
        vault_name: Name of the vault to search.
        password: Password to decrypt the vault.
        pattern: Regex or substring pattern to match against.
        search_values: If True, also search variable values.
        case_sensitive: If True, perform case-sensitive matching.

    Returns:
        A dict of matching {key: value} pairs.

    Raises:
        SearchError: If the pattern is invalid or the vault cannot be opened.
    """
    try:
        flags = 0 if case_sensitive else re.IGNORECASE
        compiled = re.compile(pattern, flags)
    except re.error as exc:
        raise SearchError(f"Invalid pattern '{pattern}': {exc}") from exc

    try:
        vault_data = load_vault(vault_name)
    except FileNotFoundError:
        raise SearchError(f"Vault '{vault_name}' does not exist.")

    try:
        decrypted = decrypt(vault_data["data"], password)
    except Exception as exc:
        raise SearchError(f"Failed to decrypt vault: {exc}") from exc

    variables: dict = json.loads(decrypted)

    results = {}
    for key, value in variables.items():
        key_match = compiled.search(key)
        value_match = search_values and compiled.search(str(value))
        if key_match or value_match:
            results[key] = value

    return results


def list_keys(vault_name: str, password: str) -> list:
    """Return a sorted list of all variable keys in a vault.

    Args:
        vault_name: Name of the vault to inspect.
        password: Password to decrypt the vault.

    Returns:
        A sorted list of variable key names.

    Raises:
        SearchError: If the vault cannot be opened or decrypted.
    """
    try:
        vault_data = load_vault(vault_name)
    except FileNotFoundError:
        raise SearchError(f"Vault '{vault_name}' does not exist.")

    try:
        decrypted = decrypt(vault_data["data"], password)
    except Exception as exc:
        raise SearchError(f"Failed to decrypt vault: {exc}") from exc

    variables: dict = json.loads(decrypted)
    return sorted(variables.keys())
