"""Tag management for vault variables."""

from typing import Dict, List, Optional
from env_vault.storage import load_vault, save_vault


class TagError(Exception):
    pass


TAGS_META_KEY = "__tags__"


def _get_tags_index(data: dict) -> Dict[str, List[str]]:
    """Return the tags index from vault data (key -> list of tags)."""
    return data.get(TAGS_META_KEY, {})


def add_tag(vault_name: str, password: str, key: str, tag: str) -> None:
    """Add a tag to a variable in the vault."""
    data = load_vault(vault_name, password)
    if key not in data and key != TAGS_META_KEY:
        raise TagError(f"Variable '{key}' not found in vault '{vault_name}'.")
    tags_index = _get_tags_index(data)
    tags_for_key = tags_index.get(key, [])
    if tag not in tags_for_key:
        tags_for_key.append(tag)
    tags_index[key] = tags_for_key
    data[TAGS_META_KEY] = tags_index
    save_vault(vault_name, password, data)


def remove_tag(vault_name: str, password: str, key: str, tag: str) -> None:
    """Remove a tag from a variable in the vault."""
    data = load_vault(vault_name, password)
    tags_index = _get_tags_index(data)
    tags_for_key = tags_index.get(key, [])
    if tag not in tags_for_key:
        raise TagError(f"Tag '{tag}' not found on variable '{key}'.")
    tags_for_key.remove(tag)
    if tags_for_key:
        tags_index[key] = tags_for_key
    else:
        tags_index.pop(key, None)
    data[TAGS_META_KEY] = tags_index
    save_vault(vault_name, password, data)


def list_tags(vault_name: str, password: str, key: Optional[str] = None) -> Dict[str, List[str]]:
    """List tags. If key is given, return tags for that key only."""
    data = load_vault(vault_name, password)
    tags_index = _get_tags_index(data)
    if key is not None:
        return {key: tags_index.get(key, [])}
    return {k: v for k, v in tags_index.items()}


def find_by_tag(vault_name: str, password: str, tag: str) -> List[str]:
    """Return all variable keys that have the given tag."""
    data = load_vault(vault_name, password)
    tags_index = _get_tags_index(data)
    return [k for k, tags in tags_index.items() if tag in tags]
