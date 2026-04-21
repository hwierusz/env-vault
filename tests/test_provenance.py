"""Tests for env_vault.provenance."""
import pytest

from env_vault.provenance import (
    ProvenanceError,
    ProvenanceEntry,
    record_provenance,
    read_provenance,
    clear_provenance,
    _provenance_path,
)


@pytest.fixture()
def vault_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("env_vault.provenance._vault_path",
                        lambda name: tmp_path / f"{name}.vault")
    (tmp_path / "myapp.vault").touch()
    return tmp_path


def test_record_provenance_returns_entry(vault_dir):
    entry = record_provenance("myapp", "DB_URL", source="CI", author="alice")
    assert isinstance(entry, ProvenanceEntry)
    assert entry.key == "DB_URL"
    assert entry.source == "CI"
    assert entry.author == "alice"


def test_record_creates_file(vault_dir):
    record_provenance("myapp", "API_KEY", source="manual", author="bob")
    path = _provenance_path("myapp")
    assert path.exists()


def test_record_empty_key_raises(vault_dir):
    with pytest.raises(ProvenanceError, match="key"):
        record_provenance("myapp", "", source="CI", author="alice")


def test_record_empty_source_raises(vault_dir):
    with pytest.raises(ProvenanceError, match="source"):
        record_provenance("myapp", "KEY", source="", author="alice")


def test_record_empty_author_raises(vault_dir):
    with pytest.raises(ProvenanceError, match="author"):
        record_provenance("myapp", "KEY", source="CI", author="")


def test_record_missing_key_in_vars_raises(vault_dir):
    with pytest.raises(ProvenanceError, match="does not exist"):
        record_provenance("myapp", "MISSING", source="CI", author="alice",
                          vars_dict={"OTHER": "val"})


def test_record_key_present_in_vars_succeeds(vault_dir):
    entry = record_provenance("myapp", "DB_URL", source="CI", author="alice",
                              vars_dict={"DB_URL": "postgres://localhost/db"})
    assert entry.key == "DB_URL"


def test_multiple_records_appended(vault_dir):
    record_provenance("myapp", "A", source="s1", author="u1")
    record_provenance("myapp", "B", source="s2", author="u2")
    entries = read_provenance("myapp")
    assert len(entries) == 2


def test_read_filters_by_key(vault_dir):
    record_provenance("myapp", "A", source="s1", author="u1")
    record_provenance("myapp", "B", source="s2", author="u2")
    entries = read_provenance("myapp", key="A")
    assert len(entries) == 1
    assert entries[0].key == "A"


def test_read_returns_empty_when_no_file(vault_dir):
    entries = read_provenance("myapp")
    assert entries == []


def test_note_stored_and_retrieved(vault_dir):
    record_provenance("myapp", "SECRET", source="vault", author="ops", note="imported from prod")
    entries = read_provenance("myapp", key="SECRET")
    assert entries[0].note == "imported from prod"


def test_clear_removes_file(vault_dir):
    record_provenance("myapp", "X", source="s", author="a")
    clear_provenance("myapp")
    assert read_provenance("myapp") == []


def test_clear_noop_when_no_file(vault_dir):
    clear_provenance("myapp")  # should not raise
