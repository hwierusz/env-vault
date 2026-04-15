"""Catalog module: tag vaults with descriptive metadata for discovery."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class CatalogError(Exception):
    """Raised when a catalog operation fails."""


@dataclass
class CatalogEntry:
    vault: str
    description: str = ""
    owner: str = ""
    tags: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"CatalogEntry(vault={self.vault!r}, owner={self.owner!r}, tags={self.tags})"

    def to_dict(self) -> Dict:
        return {
            "vault": self.vault,
            "description": self.description,
            "owner": self.owner,
            "tags": self.tags,
        }


def _get_catalog(data: dict) -> Dict[str, dict]:
    return data.setdefault("__catalog__", {})


def register_vault(
    vault_name: str,
    data: dict,
    *,
    description: str = "",
    owner: str = "",
    tags: Optional[List[str]] = None,
) -> CatalogEntry:
    """Register or update a vault entry in the catalog."""
    catalog = _get_catalog(data)
    entry = {
        "vault": vault_name,
        "description": description,
        "owner": owner,
        "tags": list(tags or []),
    }
    catalog[vault_name] = entry
    return CatalogEntry(**entry)


def unregister_vault(vault_name: str, data: dict) -> None:
    """Remove a vault from the catalog."""
    catalog = _get_catalog(data)
    if vault_name not in catalog:
        raise CatalogError(f"Vault '{vault_name}' is not in the catalog.")
    del catalog[vault_name]


def get_entry(vault_name: str, data: dict) -> Optional[CatalogEntry]:
    """Return the catalog entry for a vault, or None if absent."""
    catalog = _get_catalog(data)
    raw = catalog.get(vault_name)
    if raw is None:
        return None
    return CatalogEntry(**raw)


def list_catalog(data: dict) -> List[CatalogEntry]:
    """Return all catalog entries sorted by vault name."""
    catalog = _get_catalog(data)
    return [CatalogEntry(**v) for v in sorted(catalog.values(), key=lambda x: x["vault"])]


def search_catalog(data: dict, *, tag: Optional[str] = None, owner: Optional[str] = None) -> List[CatalogEntry]:
    """Filter catalog entries by tag and/or owner."""
    results = list_catalog(data)
    if tag:
        results = [e for e in results if tag in e.tags]
    if owner:
        results = [e for e in results if e.owner == owner]
    return results
