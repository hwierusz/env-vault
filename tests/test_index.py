"""Tests for env_vault.index."""
import pytest

from env_vault.index import IndexEntry, IndexError, build_index, query_index


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_loader(vaults: dict):
    def _load(name, password):
        return vaults[name]
    return _load


def _make_exists(names):
    def _exists(name):
        return name in names
    return _exists


ALPHA_DATA = {
    "vars": {"DB_URL": "postgres://localhost", "SECRET_KEY": "abc"},
    "tags": {"DB_URL": ["database"], "SECRET_KEY": ["secret"]},
}

BETA_DATA = {
    "vars": {"API_KEY": "xyz", "DB_URL": "mysql://remote"},
    "tags": {"API_KEY": ["api", "secret"]},
}


# ---------------------------------------------------------------------------
# build_index
# ---------------------------------------------------------------------------

def test_build_index_returns_entries_for_all_vaults():
    loader = _make_loader({"alpha": ALPHA_DATA, "beta": BETA_DATA})
    exists = _make_exists(["alpha", "beta"])
    entries = build_index(["alpha", "beta"], "pw", load_fn=loader, exists_fn=exists)
    assert len(entries) == 4


def test_build_index_entry_has_correct_vault():
    loader = _make_loader({"alpha": ALPHA_DATA})
    exists = _make_exists(["alpha"])
    entries = build_index(["alpha"], "pw", load_fn=loader, exists_fn=exists)
    assert all(e.vault == "alpha" for e in entries)


def test_build_index_entry_carries_tags():
    loader = _make_loader({"alpha": ALPHA_DATA})
    exists = _make_exists(["alpha"])
    entries = build_index(["alpha"], "pw", load_fn=loader, exists_fn=exists)
    db_entry = next(e for e in entries if e.key == "DB_URL")
    assert db_entry.tags == ["database"]


def test_build_index_missing_vault_raises():
    exists = _make_exists([])
    with pytest.raises(IndexError, match="Vault not found"):
        build_index(["missing"], "pw", load_fn=lambda n, p: {}, exists_fn=exists)


def test_build_index_load_failure_raises():
    def _bad_load(name, password):
        raise RuntimeError("decryption failed")
    exists = _make_exists(["alpha"])
    with pytest.raises(IndexError, match="Failed to load vault"):
        build_index(["alpha"], "wrong", load_fn=_bad_load, exists_fn=exists)


def test_build_index_vault_with_no_vars_returns_empty():
    loader = _make_loader({"empty": {"vars": {}, "tags": {}}})
    exists = _make_exists(["empty"])
    entries = build_index(["empty"], "pw", load_fn=loader, exists_fn=exists)
    assert entries == []


# ---------------------------------------------------------------------------
# query_index
# ---------------------------------------------------------------------------

@pytest.fixture
def all_entries():
    loader = _make_loader({"alpha": ALPHA_DATA, "beta": BETA_DATA})
    exists = _make_exists(["alpha", "beta"])
    return build_index(["alpha", "beta"], "pw", load_fn=loader, exists_fn=exists)


def test_query_no_filters_returns_all(all_entries):
    assert len(query_index(all_entries)) == 4


def test_query_by_vault(all_entries):
    results = query_index(all_entries, vault="beta")
    assert all(e.vault == "beta" for e in results)
    assert len(results) == 2


def test_query_by_key_prefix(all_entries):
    results = query_index(all_entries, key_prefix="DB")
    assert len(results) == 2
    assert all(e.key.startswith("DB") for e in results)


def test_query_by_key_prefix_case_insensitive(all_entries):
    results = query_index(all_entries, key_prefix="db")
    assert len(results) == 2


def test_query_by_tag(all_entries):
    results = query_index(all_entries, tag="secret")
    keys = {e.key for e in results}
    assert "SECRET_KEY" in keys
    assert "API_KEY" in keys


def test_query_combined_vault_and_tag(all_entries):
    results = query_index(all_entries, vault="beta", tag="secret")
    assert len(results) == 1
    assert results[0].key == "API_KEY"


def test_index_entry_to_dict():
    entry = IndexEntry(vault="alpha", key="FOO", tags=["bar"])
    d = entry.to_dict()
    assert d == {"vault": "alpha", "key": "FOO", "tags": ["bar"]}
