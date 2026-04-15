"""Tests for env_vault.trend."""
from __future__ import annotations

from typing import List

import pytest

from env_vault.trend import TrendEntry, TrendError, trend_vault


def _make_reader(events: List[dict]):
    def _reader(vault_name: str) -> List[dict]:
        return events

    return _reader


_EVENTS = [
    {"key": "DB_URL", "action": "set", "timestamp": "2024-01-01T10:00:00"},
    {"key": "DB_URL", "action": "get", "timestamp": "2024-01-01T11:00:00"},
    {"key": "DB_URL", "action": "get", "timestamp": "2024-01-01T12:00:00"},
    {"key": "API_KEY", "action": "set", "timestamp": "2024-01-01T09:00:00"},
    {"key": "API_KEY", "action": "delete", "timestamp": "2024-01-02T08:00:00"},
    {"key": "SECRET", "action": "get", "timestamp": "2024-01-01T08:00:00"},
]


def test_trend_returns_list():
    entries = trend_vault("myvault", reader=_make_reader(_EVENTS))
    assert isinstance(entries, list)
    assert len(entries) == 3


def test_trend_counts_reads():
    entries = trend_vault("myvault", reader=_make_reader(_EVENTS))
    db = next(e for e in entries if e.key == "DB_URL")
    assert db.total_reads == 2


def test_trend_counts_writes():
    entries = trend_vault("myvault", reader=_make_reader(_EVENTS))
    db = next(e for e in entries if e.key == "DB_URL")
    assert db.total_writes == 1


def test_trend_counts_deletes():
    entries = trend_vault("myvault", reader=_make_reader(_EVENTS))
    api = next(e for e in entries if e.key == "API_KEY")
    assert api.total_deletes == 1


def test_trend_sorted_by_activity_score_descending():
    entries = trend_vault("myvault", reader=_make_reader(_EVENTS))
    scores = [e.activity_score for e in entries]
    assert scores == sorted(scores, reverse=True)


def test_trend_activity_score_formula():
    entry = TrendEntry(key="X", total_reads=3, total_writes=2, total_deletes=1)
    assert entry.activity_score == 3 + 2 * 2 + 1 * 3  # 10


def test_trend_last_timestamp_is_most_recent():
    entries = trend_vault("myvault", reader=_make_reader(_EVENTS))
    db = next(e for e in entries if e.key == "DB_URL")
    assert db.last_timestamp == "2024-01-01T12:00:00"
    assert db.last_action == "get"


def test_trend_skips_events_without_key():
    events = [
        {"action": "init", "timestamp": "2024-01-01T00:00:00"},
        {"key": "FOO", "action": "set", "timestamp": "2024-01-01T01:00:00"},
    ]
    entries = trend_vault("v", reader=_make_reader(events))
    assert len(entries) == 1
    assert entries[0].key == "FOO"


def test_trend_empty_events_returns_empty_list():
    entries = trend_vault("v", reader=_make_reader([]))
    assert entries == []


def test_trend_rotate_action_counts_as_write():
    events = [{"key": "TOKEN", "action": "rotate", "timestamp": "2024-01-01T00:00:00"}]
    entries = trend_vault("v", reader=_make_reader(events))
    assert entries[0].total_writes == 1
