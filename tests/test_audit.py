"""Tests for env_vault.audit module."""

import json
import pytest
from pathlib import Path

from env_vault.audit import record_event, read_events, clear_events, _audit_path


@pytest.fixture
def vault_dir(tmp_path):
    return str(tmp_path)


def test_record_event_creates_file(vault_dir):
    record_event("myproject", "init", vault_dir=vault_dir)
    audit_file = _audit_path("myproject", vault_dir)
    assert audit_file.exists()


def test_record_event_writes_valid_json(vault_dir):
    record_event("myproject", "set", key="API_KEY", vault_dir=vault_dir)
    audit_file = _audit_path("myproject", vault_dir)
    lines = audit_file.read_text().strip().splitlines()
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["action"] == "set"
    assert event["key"] == "API_KEY"
    assert event["vault"] == "myproject"
    assert "timestamp" in event


def test_record_event_without_key(vault_dir):
    record_event("myproject", "init", vault_dir=vault_dir)
    audit_file = _audit_path("myproject", vault_dir)
    event = json.loads(audit_file.read_text().strip())
    assert "key" not in event


def test_multiple_events_appended(vault_dir):
    record_event("proj", "init", vault_dir=vault_dir)
    record_event("proj", "set", key="FOO", vault_dir=vault_dir)
    record_event("proj", "get", key="FOO", vault_dir=vault_dir)
    events = read_events("proj", vault_dir=vault_dir)
    assert len(events) == 3


def test_read_events_newest_first(vault_dir):
    record_event("proj", "init", vault_dir=vault_dir)
    record_event("proj", "set", key="BAR", vault_dir=vault_dir)
    events = read_events("proj", vault_dir=vault_dir)
    assert events[0]["action"] == "set"
    assert events[1]["action"] == "init"


def test_read_events_with_limit(vault_dir):
    for i in range(5):
        record_event("proj", "set", key=f"VAR_{i}", vault_dir=vault_dir)
    events = read_events("proj", vault_dir=vault_dir, limit=3)
    assert len(events) == 3


def test_read_events_no_file_returns_empty(vault_dir):
    events = read_events("nonexistent", vault_dir=vault_dir)
    assert events == []


def test_clear_events_removes_file(vault_dir):
    record_event("proj", "init", vault_dir=vault_dir)
    clear_events("proj", vault_dir=vault_dir)
    assert not _audit_path("proj", vault_dir).exists()


def test_clear_events_nonexistent_does_not_raise(vault_dir):
    clear_events("ghost", vault_dir=vault_dir)  # should not raise
