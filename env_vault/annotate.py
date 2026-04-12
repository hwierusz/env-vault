"""Annotation support: attach human-readable notes to vault keys."""

from __future__ import annotations

from typing import Optional

_SECTION = "__annotations__"


class AnnotateError(Exception):
    """Raised when an annotation operation fails."""


def _get_annotations(data: dict) -> dict:
    return data.setdefault(_SECTION, {})


def set_annotation(
    vault_name: str,
    key: str,
    note: str,
    load_fn,
    save_fn,
) -> None:
    """Attach *note* to *key* in the named vault."""
    data = load_fn(vault_name)
    if key not in data:
        raise AnnotateError(f"Key '{key}' not found in vault '{vault_name}'.")
    if not note.strip():
        raise AnnotateError("Annotation note must not be empty.")
    _get_annotations(data)[key] = note.strip()
    save_fn(vault_name, data)


def get_annotation(
    vault_name: str,
    key: str,
    load_fn,
) -> Optional[str]:
    """Return the annotation for *key*, or *None* if none exists."""
    data = load_fn(vault_name)
    return _get_annotations(data).get(key)


def remove_annotation(
    vault_name: str,
    key: str,
    load_fn,
    save_fn,
) -> None:
    """Remove the annotation for *key*.  Raises if no annotation exists."""
    data = load_fn(vault_name)
    annotations = _get_annotations(data)
    if key not in annotations:
        raise AnnotateError(f"No annotation found for key '{key}'.")
    del annotations[key]
    save_fn(vault_name, data)


def list_annotations(
    vault_name: str,
    load_fn,
) -> dict:
    """Return a mapping of key -> note for every annotated key."""
    data = load_fn(vault_name)
    return dict(_get_annotations(data))
