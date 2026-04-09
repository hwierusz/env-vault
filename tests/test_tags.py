"""Tests for env_vault/tags.py"""

import pytest
from unittest.mock import patch, MagicMock
from env_vault.tags import add_tag, remove_tag, list_tags, find_by_tag, TagError, TAGS_META_KEY

VAULT = "test_vault"
PASS = "secret"


def _make_data(**kwargs):
    return {"DB_URL": "postgres://", "API_KEY": "abc123", **kwargs}


@pytest.fixture
def mock_vault(monkeypatch):
    store = {"data": _make_data()}

    def fake_load(name, password):
        return dict(store["data"])

    def fake_save(name, password, data):
        store["data"] = dict(data)

    monkeypatch.setattr("env_vault.tags.load_vault", fake_load)
    monkeypatch.setattr("env_vault.tags.save_vault", fake_save)
    return store


def test_add_tag_stores_tag(mock_vault):
    add_tag(VAULT, PASS, "DB_URL", "database")
    tags = mock_vault["data"][TAGS_META_KEY]
    assert "database" in tags["DB_URL"]


def test_add_tag_multiple_tags(mock_vault):
    add_tag(VAULT, PASS, "API_KEY", "external")
    add_tag(VAULT, PASS, "API_KEY", "sensitive")
    tags = mock_vault["data"][TAGS_META_KEY]
    assert "external" in tags["API_KEY"]
    assert "sensitive" in tags["API_KEY"]


def test_add_tag_duplicate_is_idempotent(mock_vault):
    add_tag(VAULT, PASS, "DB_URL", "database")
    add_tag(VAULT, PASS, "DB_URL", "database")
    tags = mock_vault["data"][TAGS_META_KEY]
    assert tags["DB_URL"].count("database") == 1


def test_add_tag_missing_key_raises(mock_vault):
    with pytest.raises(TagError, match="not found"):
        add_tag(VAULT, PASS, "NONEXISTENT", "mytag")


def test_remove_tag(mock_vault):
    add_tag(VAULT, PASS, "DB_URL", "database")
    remove_tag(VAULT, PASS, "DB_URL", "database")
    tags = mock_vault["data"].get(TAGS_META_KEY, {})
    assert "DB_URL" not in tags


def test_remove_tag_not_present_raises(mock_vault):
    with pytest.raises(TagError, match="not found"):
        remove_tag(VAULT, PASS, "DB_URL", "ghost")


def test_list_tags_all(mock_vault):
    add_tag(VAULT, PASS, "DB_URL", "database")
    add_tag(VAULT, PASS, "API_KEY", "external")
    result = list_tags(VAULT, PASS)
    assert "DB_URL" in result
    assert "API_KEY" in result


def test_list_tags_for_key(mock_vault):
    add_tag(VAULT, PASS, "DB_URL", "database")
    result = list_tags(VAULT, PASS, key="DB_URL")
    assert result == {"DB_URL": ["database"]}


def test_list_tags_empty(mock_vault):
    result = list_tags(VAULT, PASS)
    assert result == {}


def test_find_by_tag(mock_vault):
    add_tag(VAULT, PASS, "DB_URL", "infra")
    add_tag(VAULT, PASS, "API_KEY", "infra")
    result = find_by_tag(VAULT, PASS, "infra")
    assert set(result) == {"DB_URL", "API_KEY"}


def test_find_by_tag_no_match(mock_vault):
    result = find_by_tag(VAULT, PASS, "nonexistent")
    assert result == []
