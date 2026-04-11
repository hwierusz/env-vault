"""Compare two vaults and produce a human-readable summary of differences."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from env_vault.storage import load_vault


class CompareError(Exception):
    """Raised when a vault comparison cannot be completed."""


@dataclass
class CompareResult:
    vault_a: str
    vault_b: str
    only_in_a: List[str] = field(default_factory=list)
    only_in_b: List[str] = field(default_factory=list)
    changed: List[Tuple[str, str, str]] = field(default_factory=list)  # (key, val_a, val_b)
    identical: List[str] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        return bool(self.only_in_a or self.only_in_b or self.changed)

    def summary(self) -> str:
        lines = [
            f"Comparing '{self.vault_a}' vs '{self.vault_b}'",
            f"  Only in {self.vault_a}: {len(self.only_in_a)}",
            f"  Only in {self.vault_b}: {len(self.only_in_b)}",
            f"  Changed: {len(self.changed)}",
            f"  Identical: {len(self.identical)}",
        ]
        return "\n".join(lines)


def compare_vaults(
    vault_a: str,
    password_a: str,
    vault_b: str,
    password_b: str,
    loader: Optional[Callable] = None,
) -> CompareResult:
    """Load two vaults and compare their key/value pairs.

    Args:
        vault_a: Name of the first vault.
        password_a: Password for the first vault.
        vault_b: Name of the second vault.
        password_b: Password for the second vault.
        loader: Optional callable replacing ``load_vault`` (for testing).

    Returns:
        A :class:`CompareResult` describing the differences.

    Raises:
        CompareError: If either vault cannot be loaded.
    """
    _load = loader or load_vault

    try:
        data_a: Dict[str, str] = _load(vault_a, password_a).get("vars", {})
    except Exception as exc:
        raise CompareError(f"Cannot load vault '{vault_a}': {exc}") from exc

    try:
        data_b: Dict[str, str] = _load(vault_b, password_b).get("vars", {})
    except Exception as exc:
        raise CompareError(f"Cannot load vault '{vault_b}': {exc}") from exc

    keys_a = set(data_a)
    keys_b = set(data_b)

    result = CompareResult(vault_a=vault_a, vault_b=vault_b)
    result.only_in_a = sorted(keys_a - keys_b)
    result.only_in_b = sorted(keys_b - keys_a)

    for key in sorted(keys_a & keys_b):
        if data_a[key] == data_b[key]:
            result.identical.append(key)
        else:
            result.changed.append((key, data_a[key], data_b[key]))

    return result
