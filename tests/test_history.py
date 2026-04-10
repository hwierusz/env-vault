"""Tests for env_vault.history."""

import os
import pytest

from env_vault.history import (
    HistoryError,
    clear_history,
    read_history,
    record_change,
)


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


def test_record_creates_history_file(vault_dir):
    record_change("myapp", "DB_URL", "set", vault_dir, new_value="postgres://")
    history_file = os.path.join(vault_dir, "myapp.history.jsonl")
    assert os.path.exists(history_file)


def test_record_set_contains_expected_fields(vault_dir):
    record_change("myapp", "API_KEY", "set", vault_dir, old_value="old", new_value="new")
    entries = read_history("myapp", vault_dir)
    assert len(entries) == 1
    e = entries[0]
    assert e["key"] == "API_KEY"
    assert e["action"] == "set"
    assert e["old_value"] == "old"
    assert e["new_value"] == "new"
    assert "timestamp" in e


def test_record_delete_no_value_fields(vault_dir):
    record_change("myapp", "TOKEN", "delete", vault_dir)
    entries = read_history("myapp", vault_dir)
    assert entries[0]["action"] == "delete"
    assert "old_value" not in entries[0]
    assert "new_value" not in entries[0]


def test_multiple_records_appended(vault_dir):
    for i in range(5):
        record_change("myapp", f"KEY_{i}", "set", vault_dir, new_value=str(i))
    entries = read_history("myapp", vault_dir)
    assert len(entries) == 5


def test_read_history_filter_by_key(vault_dir):
    record_change("myapp", "A", "set", vault_dir, new_value="1")
    record_change("myapp", "B", "set", vault_dir, new_value="2")
    record_change("myapp", "A", "delete", vault_dir)
    entries = read_history("myapp", vault_dir, key="A")
    assert len(entries) == 2
    assert all(e["key"] == "A" for e in entries)


def test_read_history_limit(vault_dir):
    for i in range(10):
        record_change("myapp", "X", "set", vault_dir, new_value=str(i))
    entries = read_history("myapp", vault_dir, limit=3)
    assert len(entries) == 3
    # should be the last 3
    assert entries[-1]["new_value"] == "9"


def test_read_history_missing_file_returns_empty(vault_dir):
    entries = read_history("nonexistent", vault_dir)
    assert entries == []


def test_clear_history_returns_count(vault_dir):
    for i in range(4):
        record_change("myapp", "K", "set", vault_dir, new_value=str(i))
    removed = clear_history("myapp", vault_dir)
    assert removed == 4


def test_clear_history_removes_file(vault_dir):
    record_change("myapp", "K", "set", vault_dir, new_value="v")
    clear_history("myapp", vault_dir)
    assert read_history("myapp", vault_dir) == []


def test_clear_history_nonexistent_returns_zero(vault_dir):
    assert clear_history("ghost", vault_dir) == 0


def test_record_invalid_action_raises(vault_dir):
    with pytest.raises(HistoryError, match="Unknown action"):
        record_change("myapp", "KEY", "update", vault_dir)
