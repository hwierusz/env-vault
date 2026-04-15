"""Tests for env_vault.catalog."""
import pytest
from env_vault.catalog import (
    CatalogError,
    CatalogEntry,
    register_vault,
    unregister_vault,
    get_entry,
    list_catalog,
    search_catalog,
)


def _base():
    return {"SOME_KEY": "value"}


def test_register_vault_stores_entry():
    data = _base()
    entry = register_vault("myapp", data, description="Main app", owner="alice", tags=["prod"])
    assert isinstance(entry, CatalogEntry)
    assert entry.vault == "myapp"
    assert entry.owner == "alice"
    assert "prod" in entry.tags
    assert data["__catalog__"]["myapp"]["description"] == "Main app"


def test_register_vault_defaults():
    data = _base()
    entry = register_vault("svc", data)
    assert entry.description == ""
    assert entry.owner == ""
    assert entry.tags == []


def test_register_vault_overwrites_existing():
    data = _base()
    register_vault("svc", data, owner="alice")
    register_vault("svc", data, owner="bob")
    assert data["__catalog__"]["svc"]["owner"] == "bob"


def test_unregister_vault_removes_entry():
    data = _base()
    register_vault("svc", data)
    unregister_vault("svc", data)
    assert "svc" not in data["__catalog__"]


def test_unregister_missing_vault_raises():
    data = _base()
    with pytest.raises(CatalogError, match="not in the catalog"):
        unregister_vault("ghost", data)


def test_get_entry_returns_entry():
    data = _base()
    register_vault("svc", data, owner="carol")
    entry = get_entry("svc", data)
    assert entry is not None
    assert entry.owner == "carol"


def test_get_entry_missing_returns_none():
    data = _base()
    assert get_entry("nope", data) is None


def test_list_catalog_sorted():
    data = _base()
    register_vault("z_vault", data)
    register_vault("a_vault", data)
    entries = list_catalog(data)
    assert [e.vault for e in entries] == ["a_vault", "z_vault"]


def test_list_catalog_empty():
    data = _base()
    assert list_catalog(data) == []


def test_search_catalog_by_tag():
    data = _base()
    register_vault("prod_svc", data, tags=["prod", "critical"])
    register_vault("dev_svc", data, tags=["dev"])
    results = search_catalog(data, tag="prod")
    assert len(results) == 1
    assert results[0].vault == "prod_svc"


def test_search_catalog_by_owner():
    data = _base()
    register_vault("svc1", data, owner="alice")
    register_vault("svc2", data, owner="bob")
    results = search_catalog(data, owner="alice")
    assert len(results) == 1
    assert results[0].vault == "svc1"


def test_search_catalog_combined_filters():
    data = _base()
    register_vault("svc1", data, owner="alice", tags=["prod"])
    register_vault("svc2", data, owner="alice", tags=["dev"])
    results = search_catalog(data, owner="alice", tag="prod")
    assert len(results) == 1
    assert results[0].vault == "svc1"


def test_catalog_entry_repr():
    e = CatalogEntry(vault="v", owner="o", tags=["t"])
    assert "v" in repr(e)
    assert "o" in repr(e)


def test_catalog_entry_to_dict():
    e = CatalogEntry(vault="v", description="d", owner="o", tags=["a", "b"])
    d = e.to_dict()
    assert d["vault"] == "v"
    assert d["tags"] == ["a", "b"]
