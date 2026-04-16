"""Tests for env_vault.traceback."""
import os
import pytest
from env_vault.traceback import (
    record_trace,
    read_traces,
    clear_traces,
    TracebackError,
    TraceEntry,
)


@pytest.fixture
def vault_dir(tmp_path):
    return str(tmp_path)


def test_record_trace_creates_file(vault_dir):
    record_trace(vault_dir, "myapp", "DB_URL", "postgres://", "import")
    path = os.path.join(vault_dir, "myapp.trace.jsonl")
    assert os.path.exists(path)


def test_record_trace_returns_entry(vault_dir):
    entry = record_trace(vault_dir, "myapp", "DB_URL", "postgres://", "import", note="initial")
    assert isinstance(entry, TraceEntry)
    assert entry.key == "DB_URL"
    assert entry.source == "import"
    assert entry.note == "initial"


def test_record_trace_empty_key_raises(vault_dir):
    with pytest.raises(TracebackError, match="key"):
        record_trace(vault_dir, "myapp", "", "val", "cli")


def test_record_trace_empty_source_raises(vault_dir):
    with pytest.raises(TracebackError, match="source"):
        record_trace(vault_dir, "myapp", "KEY", "val", "")


def test_read_traces_empty_when_no_file(vault_dir):
    assert read_traces(vault_dir, "ghost") == []


def test_multiple_entries_appended(vault_dir):
    record_trace(vault_dir, "myapp", "A", "1", "cli")
    record_trace(vault_dir, "myapp", "B", "2", "import")
    entries = read_traces(vault_dir, "myapp")
    assert len(entries) == 2
    assert entries[0].key == "A"
    assert entries[1].key == "B"


def test_filter_by_key(vault_dir):
    record_trace(vault_dir, "myapp", "A", "1", "cli")
    record_trace(vault_dir, "myapp", "B", "2", "cli")
    record_trace(vault_dir, "myapp", "A", "3", "api")
    entries = read_traces(vault_dir, "myapp", key="A")
    assert len(entries) == 2
    assert all(e.key == "A" for e in entries)


def test_entry_has_timestamp(vault_dir):
    entry = record_trace(vault_dir, "myapp", "X", "v", "src")
    assert entry.timestamp
    assert "T" in entry.timestamp


def test_clear_traces_returns_count(vault_dir):
    record_trace(vault_dir, "myapp", "A", "1", "cli")
    record_trace(vault_dir, "myapp", "B", "2", "cli")
    count = clear_traces(vault_dir, "myapp")
    assert count == 2


def test_clear_traces_removes_file(vault_dir):
    record_trace(vault_dir, "myapp", "A", "1", "cli")
    clear_traces(vault_dir, "myapp")
    path = os.path.join(vault_dir, "myapp.trace.jsonl")
    assert not os.path.exists(path)


def test_clear_traces_nonexistent_returns_zero(vault_dir):
    assert clear_traces(vault_dir, "ghost") == 0


def test_to_dict_contains_all_fields(vault_dir):
    entry = record_trace(vault_dir, "myapp", "K", "v", "src", note="n")
    d = entry.to_dict()
    assert set(d.keys()) == {"key", "value", "source", "timestamp", "note"}
