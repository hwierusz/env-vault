"""Rollback support: revert a vault to a previous history entry."""

from __future__ import annotations

from typing import Callable, Dict, List, Optional

from env_vault.history import read_history, HistoryError


class RollbackError(Exception):
    """Raised when a rollback operation fails."""


def list_rollback_points(
    vault_name: str,
    vault_dir: str = ".",
) -> List[dict]:
    """Return history entries that can be rolled back to.

    Each entry contains at least: index, timestamp, action, key.
    """
    try:
        events = read_history(vault_name, vault_dir=vault_dir)
    except HistoryError as exc:
        raise RollbackError(str(exc)) from exc
    return [{"index": i, **e} for i, e in enumerate(events)]


def rollback_to(
    vault_name: str,
    index: int,
    *,
    load_fn: Callable[[str], Dict[str, str]],
    save_fn: Callable[[str, Dict[str, str]], None],
    vault_dir: str = ".",
) -> Dict[str, str]:
    """Replay history up to *index* (inclusive) to rebuild vault state.

    Returns the reconstructed variable mapping.
    Raises RollbackError if index is out of range or history is unavailable.
    """
    try:
        events = read_history(vault_name, vault_dir=vault_dir)
    except HistoryError as exc:
        raise RollbackError(str(exc)) from exc

    if not events:
        raise RollbackError(f"No history found for vault '{vault_name}'.")

    if index < 0 or index >= len(events):
        raise RollbackError(
            f"Index {index} out of range (0–{len(events) - 1})."
        )

    state: Dict[str, str] = {}
    for event in events[: index + 1]:
        action = event.get("action")
        key = event.get("key")
        value = event.get("value")
        if action == "set" and key is not None and value is not None:
            state[key] = value
        elif action == "delete" and key is not None:
            state.pop(key, None)

    save_fn(vault_name, state)
    return state
