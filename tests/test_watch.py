"""Tests for env_vault.watch."""

from __future__ import annotations

import threading
from typing import Dict

import pytest

from env_vault.watch import (
    WatchError,
    WatchEvent,
    _diff_snapshots,
    watch_vault,
)


# ---------------------------------------------------------------------------
# _diff_snapshots
# ---------------------------------------------------------------------------

def test_diff_added_key():
    event = _diff_snapshots({"A": "1"}, {"A": "1", "B": "2"})
    assert event.added == {"B": "2"}
    assert event.removed == []
    assert event.changed == {}


def test_diff_removed_key():
    event = _diff_snapshots({"A": "1", "B": "2"}, {"A": "1"})
    assert event.removed == ["B"]
    assert event.added == {}
    assert event.changed == {}


def test_diff_changed_key():
    event = _diff_snapshots({"A": "old"}, {"A": "new"})
    assert event.changed == {"A": "new"}
    assert event.added == {}
    assert event.removed == []


def test_diff_no_changes():
    event = _diff_snapshots({"A": "1"}, {"A": "1"})
    assert not event.has_changes


def test_has_changes_true_when_added():
    event = WatchEvent(vault_name="v", added={"X": "1"})
    assert event.has_changes


# ---------------------------------------------------------------------------
# watch_vault
# ---------------------------------------------------------------------------

def _make_load(snapshots):
    """Return a load_fn that cycles through *snapshots* on successive calls."""
    it = iter(snapshots)

    def _load(name, pw):
        return next(it)

    return _load


def test_watch_raises_if_vault_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("env_vault.watch.vault_exists", lambda _: False)
    with pytest.raises(WatchError, match="does not exist"):
        watch_vault("ghost", "pw", callback=lambda e: None)


def test_watch_raises_if_initial_load_fails(monkeypatch):
    monkeypatch.setattr("env_vault.watch.vault_exists", lambda _: True)

    def bad_load(name, pw):
        raise RuntimeError("bad decrypt")

    with pytest.raises(WatchError, match="Cannot read vault"):
        watch_vault("v", "pw", callback=lambda e: None, load_fn=bad_load)


def test_watch_detects_change(monkeypatch):
    monkeypatch.setattr("env_vault.watch.vault_exists", lambda _: True)
    monkeypatch.setattr("env_vault.watch.time.sleep", lambda _: None)

    snapshots = [
        {"A": "1"},          # initial load
        {"A": "1", "B": "2"}, # first poll — change detected
    ]
    load_fn = _make_load(snapshots)

    events = []
    stop = threading.Event()

    def callback(event: WatchEvent):
        events.append(event)
        stop.set()  # stop after first change

    watch_vault("v", "pw", callback=callback, interval=0, stop_event=stop, load_fn=load_fn)

    assert len(events) == 1
    assert events[0].added == {"B": "2"}
    assert events[0].vault_name == "v"


def test_watch_skips_failed_poll(monkeypatch):
    monkeypatch.setattr("env_vault.watch.vault_exists", lambda _: True)
    monkeypatch.setattr("env_vault.watch.time.sleep", lambda _: None)

    call_count = 0
    stop = threading.Event()

    def load_fn(name, pw):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return {"A": "1"}  # initial
        if call_count == 2:
            raise RuntimeError("transient error")
        stop.set()
        return {"A": "1"}  # no change on third

    events = []
    watch_vault("v", "pw", callback=lambda e: events.append(e),
                interval=0, stop_event=stop, load_fn=load_fn)

    assert events == []  # no change events despite transient error
