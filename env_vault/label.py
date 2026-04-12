"""Label management for vault variables.

Labels are free-form string tags attached to keys for categorisation,
filtering, and documentation purposes.  Unlike namespaces or groups,
a key may carry an arbitrary number of labels and labels carry no
structural meaning.
"""

from __future__ import annotations

from typing import Callable, Dict, List


class LabelError(Exception):
    """Raised when a label operation fails."""


def _get_labels(data: dict) -> dict:
    return data.setdefault("__labels__", {})


def add_label(
    vault_name: str,
    key: str,
    label: str,
    load: Callable,
    save: Callable,
) -> None:
    """Attach *label* to *key* inside *vault_name*."""
    data = load(vault_name)
    if key not in data.get("vars", {}):
        raise LabelError(f"Key '{key}' not found in vault '{vault_name}'.")
    labels = _get_labels(data)
    key_labels: List[str] = labels.setdefault(key, [])
    if label not in key_labels:
        key_labels.append(label)
    save(vault_name, data)


def remove_label(
    vault_name: str,
    key: str,
    label: str,
    load: Callable,
    save: Callable,
) -> None:
    """Detach *label* from *key*.  Silently succeeds if label absent."""
    data = load(vault_name)
    labels = _get_labels(data)
    key_labels: List[str] = labels.get(key, [])
    if label in key_labels:
        key_labels.remove(label)
        labels[key] = key_labels
    save(vault_name, data)


def list_labels(
    vault_name: str,
    key: str,
    load: Callable,
) -> List[str]:
    """Return all labels attached to *key*."""
    data = load(vault_name)
    return list(_get_labels(data).get(key, []))


def find_by_label(
    vault_name: str,
    label: str,
    load: Callable,
) -> Dict[str, List[str]]:
    """Return mapping of key -> labels for every key carrying *label*."""
    data = load(vault_name)
    result: Dict[str, List[str]] = {}
    for k, lbls in _get_labels(data).items():
        if label in lbls:
            result[k] = list(lbls)
    return result
