"""Tests for env_vault.diff module."""

import pytest

from env_vault.diff import DiffEntry, DiffError, diff_vault_against_dict, diff_vaults
from env_vault.storage import save_vault


PASSWORD = "test-secret"


@pytest.fixture()
def vault_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("ENV_VAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def two_vaults(vault_dir):
    save_vault("left", PASSWORD, {"A": "1", "B": "2", "C": "3"})
    save_vault("right", PASSWORD, {"A": "1", "B": "99", "D": "4"})


def test_diff_vaults_changed_key(vault_dir, two_vaults):
    entries = diff_vaults("left", PASSWORD, "right", PASSWORD)
    changed = [e for e in entries if e.status == "changed"]
    assert len(changed) == 1
    assert changed[0].key == "B"
    assert changed[0].left_value == "2"
    assert changed[0].right_value == "99"


def test_diff_vaults_removed_key(vault_dir, two_vaults):
    entries = diff_vaults("left", PASSWORD, "right", PASSWORD)
    removed = [e for e in entries if e.status == "removed"]
    assert len(removed) == 1
    assert removed[0].key == "C"
    assert removed[0].right_value is None


def test_diff_vaults_added_key(vault_dir, two_vaults):
    entries = diff_vaults("left", PASSWORD, "right", PASSWORD)
    added = [e for e in entries if e.status == "added"]
    assert len(added) == 1
    assert added[0].key == "D"
    assert added[0].left_value is None


def test_diff_vaults_unchanged_hidden_by_default(vault_dir, two_vaults):
    entries = diff_vaults("left", PASSWORD, "right", PASSWORD)
    assert not any(e.status == "unchanged" for e in entries)


def test_diff_vaults_show_unchanged(vault_dir, two_vaults):
    entries = diff_vaults("left", PASSWORD, "right", PASSWORD, show_unchanged=True)
    unchanged = [e for e in entries if e.status == "unchanged"]
    assert len(unchanged) == 1
    assert unchanged[0].key == "A"


def test_diff_vaults_missing_left_raises(vault_dir):
    save_vault("right", PASSWORD, {"X": "1"})
    with pytest.raises(DiffError, match="'ghost'"):
        diff_vaults("ghost", PASSWORD, "right", PASSWORD)


def test_diff_vaults_missing_right_raises(vault_dir):
    save_vault("left", PASSWORD, {"X": "1"})
    with pytest.raises(DiffError, match="'ghost'"):
        diff_vaults("left", PASSWORD, "ghost", PASSWORD)


def test_diff_vault_against_dict(vault_dir):
    save_vault("myapp", PASSWORD, {"HOST": "localhost", "PORT": "5432"})
    other = {"HOST": "localhost", "PORT": "5433", "DEBUG": "true"}
    entries = diff_vault_against_dict("myapp", PASSWORD, other)

    statuses = {e.key: e.status for e in entries}
    assert statuses["PORT"] == "changed"
    assert statuses["DEBUG"] == "added"
    assert "HOST" not in statuses  # unchanged, hidden by default


def test_diff_vault_against_dict_missing_vault_raises(vault_dir):
    with pytest.raises(DiffError, match="'nowhere'"):
        diff_vault_against_dict("nowhere", PASSWORD, {"A": "1"})


def test_diff_entry_repr_fields():
    entry = DiffEntry(key="FOO", status="changed", left_value="old", right_value="new")
    assert entry.key == "FOO"
    assert entry.status == "changed"
    assert entry.left_value == "old"
    assert entry.right_value == "new"
