"""Tests for env_vault.rollback."""

from __future__ import annotations

import pytest

from env_vault.rollback import list_rollback_points, rollback_to, RollbackError


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_history_reader(events):
    """Return a patcher target and side-effect list."""
    return events


def _noop_save(name, data):
    pass


# ---------------------------------------------------------------------------
# list_rollback_points
# ---------------------------------------------------------------------------

def test_list_rollback_points_returns_indexed_entries(monkeypatch):
    events = [
        {"timestamp": "2024-01-01T00:00:00", "action": "set", "key": "FOO", "value": "1"},
        {"timestamp": "2024-01-02T00:00:00", "action": "set", "key": "BAR", "value": "2"},
    ]
    monkeypatch.setattr("env_vault.rollback.read_history", lambda name, vault_dir: events)
    points = list_rollback_points("myvault")
    assert len(points) == 2
    assert points[0]["index"] == 0
    assert points[1]["index"] == 1


def test_list_rollback_points_raises_on_history_error(monkeypatch):
    from env_vault.history import HistoryError
    monkeypatch.setattr(
        "env_vault.rollback.read_history",
        lambda name, vault_dir: (_ for _ in ()).throw(HistoryError("bad")),
    )
    with pytest.raises(RollbackError):
        list_rollback_points("myvault")


# ---------------------------------------------------------------------------
# rollback_to
# ---------------------------------------------------------------------------

def _patch_history(monkeypatch, events):
    monkeypatch.setattr("env_vault.rollback.read_history", lambda name, vault_dir: events)


def test_rollback_to_replays_set_events(monkeypatch):
    events = [
        {"action": "set", "key": "A", "value": "1"},
        {"action": "set", "key": "B", "value": "2"},
        {"action": "set", "key": "C", "value": "3"},
    ]
    _patch_history(monkeypatch, events)
    saved = {}

    def fake_save(name, data):
        saved.update(data)

    state = rollback_to("v", 1, load_fn=lambda n: {}, save_fn=fake_save)
    assert state == {"A": "1", "B": "2"}
    assert saved == {"A": "1", "B": "2"}


def test_rollback_to_handles_delete_events(monkeypatch):
    events = [
        {"action": "set", "key": "A", "value": "1"},
        {"action": "set", "key": "B", "value": "2"},
        {"action": "delete", "key": "A"},
    ]
    _patch_history(monkeypatch, events)
    state = rollback_to("v", 2, load_fn=lambda n: {}, save_fn=_noop_save)
    assert "A" not in state
    assert state["B"] == "2"


def test_rollback_to_index_zero_gives_first_event(monkeypatch):
    events = [
        {"action": "set", "key": "X", "value": "42"},
        {"action": "set", "key": "Y", "value": "99"},
    ]
    _patch_history(monkeypatch, events)
    state = rollback_to("v", 0, load_fn=lambda n: {}, save_fn=_noop_save)
    assert state == {"X": "42"}


def test_rollback_to_raises_for_out_of_range_index(monkeypatch):
    events = [{"action": "set", "key": "A", "value": "1"}]
    _patch_history(monkeypatch, events)
    with pytest.raises(RollbackError, match="out of range"):
        rollback_to("v", 5, load_fn=lambda n: {}, save_fn=_noop_save)


def test_rollback_to_raises_for_empty_history(monkeypatch):
    _patch_history(monkeypatch, [])
    with pytest.raises(RollbackError, match="No history"):
        rollback_to("v", 0, load_fn=lambda n: {}, save_fn=_noop_save)


def test_rollback_to_negative_index_raises(monkeypatch):
    events = [{"action": "set", "key": "A", "value": "1"}]
    _patch_history(monkeypatch, events)
    with pytest.raises(RollbackError):
        rollback_to("v", -1, load_fn=lambda n: {}, save_fn=_noop_save)
