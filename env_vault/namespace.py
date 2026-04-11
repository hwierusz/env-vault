"""Namespace support for grouping environment variables within a vault."""

from typing import Dict, List, Optional

NAMESPACE_KEY = "__namespaces__"
DEFAULT_NS = "default"


class NamespaceError(Exception):
    pass


def _get_namespaces(data: dict) -> Dict[str, List[str]]:
    """Return the namespace index from vault data."""
    return data.get(NAMESPACE_KEY, {})


def assign_to_namespace(
    vault_name: str,
    key: str,
    namespace: str,
    load_fn,
    save_fn,
    password: str,
) -> None:
    """Assign an existing vault key to a namespace."""
    data = load_fn(vault_name, password)
    if key not in data:
        raise NamespaceError(f"Key '{key}' not found in vault '{vault_name}'.")
    if not namespace or not namespace.isidentifier():
        raise NamespaceError(f"Invalid namespace name: '{namespace}'.")
    ns_index: Dict[str, List[str]] = _get_namespaces(data)
    # Remove key from any existing namespace
    for ns_keys in ns_index.values():
        if key in ns_keys:
            ns_keys.remove(key)
    ns_index.setdefault(namespace, []).append(key)
    data[NAMESPACE_KEY] = ns_index
    save_fn(vault_name, password, data)


def remove_from_namespace(
    vault_name: str,
    key: str,
    namespace: str,
    load_fn,
    save_fn,
    password: str,
) -> None:
    """Remove a key from a namespace (moves it back to unassigned)."""
    data = load_fn(vault_name, password)
    ns_index = _get_namespaces(data)
    if namespace not in ns_index or key not in ns_index[namespace]:
        raise NamespaceError(f"Key '{key}' is not in namespace '{namespace}'.")
    ns_index[namespace].remove(key)
    if not ns_index[namespace]:
        del ns_index[namespace]
    data[NAMESPACE_KEY] = ns_index
    save_fn(vault_name, password, data)


def list_namespaces(vault_name: str, load_fn, password: str) -> Dict[str, List[str]]:
    """Return all namespaces and their associated keys."""
    data = load_fn(vault_name, password)
    return {k: list(v) for k, v in _get_namespaces(data).items()}


def get_namespace_vars(
    vault_name: str,
    namespace: str,
    load_fn,
    password: str,
) -> Dict[str, str]:
    """Return key/value pairs for all keys in a given namespace."""
    data = load_fn(vault_name, password)
    ns_index = _get_namespaces(data)
    if namespace not in ns_index:
        raise NamespaceError(f"Namespace '{namespace}' does not exist.")
    return {k: data[k] for k in ns_index[namespace] if k in data}
