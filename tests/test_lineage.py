"""Tests for env_vault.lineage."""
import pytest

from env_vault.lineage import (
    LineageError,
    LineageEntry,
    record_lineage,
    get_lineage,
    list_lineage,
    remove_lineage,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_data():
    return {"vars": {"API_KEY": "secret", "DB_URL": "postgres://localhost/db"}}


def _make_load(store: dict):
    def _load(name: str) -> dict:
        return store[name]
    return _load


def _make_save(store: dict):
    def _save(name: str, data: dict) -> None:
        store[name] = data
    return _save


@pytest.fixture()
def store():
    data = _base_data()
    # Flatten vars to top-level so record_lineage can find keys
    data.update(data.pop("vars"))
    return {"myvault": data}


# ---------------------------------------------------------------------------
# record_lineage
# ---------------------------------------------------------------------------

def test_record_lineage_returns_entry(store):
    entry = record_lineage(
        "myvault", "API_KEY", "external-service",
        load=_make_load(store), save=_make_save(store),
    )
    assert isinstance(entry, LineageEntry)
    assert entry.key == "API_KEY"
    assert entry.source == "external-service"


def test_record_lineage_stores_in_vault(store):
    record_lineage(
        "myvault", "DB_URL", "infra-team", note="provisioned via Terraform",
        load=_make_load(store), save=_make_save(store),
    )
    lineage_section = store["myvault"]["__lineage__"]
    assert "DB_URL" in lineage_section
    assert lineage_section["DB_URL"]["note"] == "provisioned via Terraform"


def test_record_lineage_with_derived_from(store):
    entry = record_lineage(
        "myvault", "API_KEY", "rotate-job", derived_from="OLD_API_KEY",
        load=_make_load(store), save=_make_save(store),
    )
    assert entry.derived_from == "OLD_API_KEY"


def test_record_lineage_missing_key_raises(store):
    with pytest.raises(LineageError, match="MISSING_KEY"):
        record_lineage(
            "myvault", "MISSING_KEY", "somewhere",
            load=_make_load(store), save=_make_save(store),
        )


# ---------------------------------------------------------------------------
# get_lineage
# ---------------------------------------------------------------------------

def test_get_lineage_returns_none_when_not_recorded(store):
    result = get_lineage("myvault", "API_KEY", load=_make_load(store))
    assert result is None


def test_get_lineage_returns_entry_after_record(store):
    record_lineage(
        "myvault", "API_KEY", "ci-pipeline",
        load=_make_load(store), save=_make_save(store),
    )
    entry = get_lineage("myvault", "API_KEY", load=_make_load(store))
    assert entry is not None
    assert entry.source == "ci-pipeline"


# ---------------------------------------------------------------------------
# list_lineage
# ---------------------------------------------------------------------------

def test_list_lineage_empty(store):
    entries = list_lineage("myvault", load=_make_load(store))
    assert entries == []


def test_list_lineage_multiple_entries(store):
    ld, sv = _make_load(store), _make_save(store)
    record_lineage("myvault", "API_KEY", "svc-a", load=ld, save=sv)
    record_lineage("myvault", "DB_URL", "svc-b", load=ld, save=sv)
    entries = list_lineage("myvault", load=ld)
    keys = {e.key for e in entries}
    assert keys == {"API_KEY", "DB_URL"}


# ---------------------------------------------------------------------------
# remove_lineage
# ---------------------------------------------------------------------------

def test_remove_lineage_returns_true_when_existed(store):
    ld, sv = _make_load(store), _make_save(store)
    record_lineage("myvault", "API_KEY", "origin", load=ld, save=sv)
    assert remove_lineage("myvault", "API_KEY", load=ld, save=sv) is True


def test_remove_lineage_returns_false_when_absent(store):
    ld, sv = _make_load(store), _make_save(store)
    assert remove_lineage("myvault", "API_KEY", load=ld, save=sv) is False


def test_remove_lineage_actually_removes(store):
    ld, sv = _make_load(store), _make_save(store)
    record_lineage("myvault", "API_KEY", "origin", load=ld, save=sv)
    remove_lineage("myvault", "API_KEY", load=ld, save=sv)
    assert get_lineage("myvault", "API_KEY", load=ld) is None
