"""Index module: build and query a searchable key index across multiple vaults."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from env_vault.storage import load_vault, vault_exists


class IndexError(Exception):
    """Raised when an index operation fails."""


@dataclass
class IndexEntry:
    vault: str
    key: str
    tags: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return f"IndexEntry(vault={self.vault!r}, key={self.key!r})"

    def to_dict(self) -> Dict:
        return {"vault": self.vault, "key": self.key, "tags": self.tags}


def build_index(
    vault_names: List[str],
    password: str,
    load_fn=None,
    exists_fn=None,
) -> List[IndexEntry]:
    """Build an index of all keys across the given vaults.

    Args:
        vault_names: List of vault names to index.
        password: Decryption password (same for all vaults).
        load_fn: Optional override for load_vault (for testing).
        exists_fn: Optional override for vault_exists (for testing).

    Returns:
        List of IndexEntry objects.

    Raises:
        IndexError: If a vault cannot be loaded.
    """
    _load = load_fn or load_vault
    _exists = exists_fn or vault_exists

    entries: List[IndexEntry] = []
    for name in vault_names:
        if not _exists(name):
            raise IndexError(f"Vault not found: {name!r}")
        try:
            data = _load(name, password)
        except Exception as exc:
            raise IndexError(f"Failed to load vault {name!r}: {exc}") from exc

        vars_section: Dict[str, str] = data.get("vars", {})
        tags_section: Dict[str, List[str]] = data.get("tags", {})

        for key in vars_section:
            entry = IndexEntry(
                vault=name,
                key=key,
                tags=list(tags_section.get(key, [])),
            )
            entries.append(entry)

    return entries


def query_index(
    entries: List[IndexEntry],
    key_prefix: Optional[str] = None,
    tag: Optional[str] = None,
    vault: Optional[str] = None,
) -> List[IndexEntry]:
    """Filter index entries by optional criteria."""
    results = entries
    if vault is not None:
        results = [e for e in results if e.vault == vault]
    if key_prefix is not None:
        prefix_lower = key_prefix.lower()
        results = [e for e in results if e.key.lower().startswith(prefix_lower)]
    if tag is not None:
        tag_lower = tag.lower()
        results = [e for e in results if tag_lower in [t.lower() for t in e.tags]]
    return results
