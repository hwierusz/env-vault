"""Tests for env_vault.group."""

from __future__ import annotations

import pytest

from env_vault.group import (
    GroupError,
    add_to_group,
    delete_group,
    get_group_members,
    get_vars_for_group,
    list_groups,
    remove_from_group,
)


def _base_data() -> dict:
    return {"DB_URL": "postgres://localhost", "API_KEY": "secret", "PORT": "5432"}


def test_add_to_group_stores_key():
    data = _base_data()
    add_to_group(data, "database", "DB_URL")
    assert "DB_URL" in data["__groups__"]["database"]


def test_add_multiple_keys_to_group():
    data = _base_data()
    add_to_group(data, "database", "DB_URL")
    add_to_group(data, "database", "PORT")
    assert data["__groups__"]["database"] == ["DB_URL", "PORT"]


def test_add_duplicate_key_is_idempotent():
    data = _base_data()
    add_to_group(data, "database", "DB_URL")
    add_to_group(data, "database", "DB_URL")
    assert data["__groups__"]["database"].count("DB_URL") == 1


def test_add_missing_key_raises():
    data = _base_data()
    with pytest.raises(GroupError, match="does not exist"):
        add_to_group(data, "database", "MISSING_KEY")


def test_add_empty_group_name_raises():
    data = _base_data()
    with pytest.raises(GroupError, match="must not be empty"):
        add_to_group(data, "", "DB_URL")


def test_remove_from_group_removes_key():
    data = _base_data()
    add_to_group(data, "database", "DB_URL")
    add_to_group(data, "database", "PORT")
    remove_from_group(data, "database", "DB_URL")
    assert "DB_URL" not in data["__groups__"]["database"]


def test_remove_last_key_deletes_group():
    data = _base_data()
    add_to_group(data, "database", "DB_URL")
    remove_from_group(data, "database", "DB_URL")
    assert "database" not in data["__groups__"]


def test_remove_from_nonexistent_group_raises():
    data = _base_data()
    with pytest.raises(GroupError, match="does not exist"):
        remove_from_group(data, "ghost", "DB_URL")


def test_remove_key_not_in_group_raises():
    data = _base_data()
    add_to_group(data, "database", "DB_URL")
    with pytest.raises(GroupError, match="not in group"):
        remove_from_group(data, "database", "API_KEY")


def test_list_groups_returns_sorted():
    data = _base_data()
    add_to_group(data, "z_group", "DB_URL")
    add_to_group(data, "a_group", "API_KEY")
    assert list_groups(data) == ["a_group", "z_group"]


def test_list_groups_empty_when_none():
    data = _base_data()
    assert list_groups(data) == []


def test_get_group_members_returns_list():
    data = _base_data()
    add_to_group(data, "web", "API_KEY")
    add_to_group(data, "web", "PORT")
    assert get_group_members(data, "web") == ["API_KEY", "PORT"]


def test_get_group_members_nonexistent_raises():
    data = _base_data()
    with pytest.raises(GroupError, match="does not exist"):
        get_group_members(data, "nope")


def test_get_vars_for_group_returns_values():
    data = _base_data()
    add_to_group(data, "database", "DB_URL")
    add_to_group(data, "database", "PORT")
    result = get_vars_for_group(data, "database")
    assert result == {"DB_URL": "postgres://localhost", "PORT": "5432"}


def test_delete_group_removes_group():
    data = _base_data()
    add_to_group(data, "temp", "DB_URL")
    delete_group(data, "temp")
    assert "temp" not in data.get("__groups__", {})


def test_delete_nonexistent_group_raises():
    data = _base_data()
    with pytest.raises(GroupError, match="does not exist"):
        delete_group(data, "ghost")
