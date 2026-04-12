"""Tests for env_vault.visibility."""

import pytest

from env_vault.visibility import (
    VisibilityError,
    filter_by_visibility,
    get_visibility,
    list_visibility,
    remove_visibility,
    set_visibility,
)


@pytest.fixture()
def data():
    return {
        "vars": {
            "API_KEY": "secret",
            "APP_ENV": "production",
            "DEBUG": "false",
        }
    }


def test_set_visibility_stores_level(data):
    set_visibility(data, "API_KEY", "hidden")
    assert data["__visibility__"]["API_KEY"] == "hidden"


def test_set_visibility_invalid_level_raises(data):
    with pytest.raises(VisibilityError, match="Invalid visibility level"):
        set_visibility(data, "API_KEY", "top-secret")


def test_set_visibility_missing_key_raises(data):
    with pytest.raises(VisibilityError, match="not found"):
        set_visibility(data, "NONEXISTENT", "public")


def test_set_visibility_overwrites_existing_level(data):
    set_visibility(data, "API_KEY", "hidden")
    set_visibility(data, "API_KEY", "public")
    assert data["__visibility__"]["API_KEY"] == "public"


def test_get_visibility_returns_default_private(data):
    assert get_visibility(data, "APP_ENV") == "private"


def test_get_visibility_returns_stored_level(data):
    set_visibility(data, "DEBUG", "public")
    assert get_visibility(data, "DEBUG") == "public"


def test_remove_visibility_clears_entry(data):
    set_visibility(data, "API_KEY", "hidden")
    remove_visibility(data, "API_KEY")
    assert "API_KEY" not in data.get("__visibility__", {})


def test_remove_visibility_missing_raises(data):
    with pytest.raises(VisibilityError, match="No visibility setting"):
        remove_visibility(data, "APP_ENV")


def test_filter_by_visibility_exact(data):
    set_visibility(data, "API_KEY", "hidden")
    set_visibility(data, "DEBUG", "public")
    # APP_ENV defaults to private
    result = filter_by_visibility(data, "private")
    assert "APP_ENV" in result
    assert "API_KEY" not in result
    assert "DEBUG" not in result


def test_filter_by_visibility_include_higher(data):
    set_visibility(data, "API_KEY", "hidden")
    set_visibility(data, "DEBUG", "public")
    # include_higher=True for 'private' should include public + private
    result = filter_by_visibility(data, "private", include_higher=True)
    assert "DEBUG" in result
    assert "APP_ENV" in result
    assert "API_KEY" not in result


def test_filter_by_visibility_invalid_level_raises(data):
    with pytest.raises(VisibilityError, match="Invalid visibility level"):
        filter_by_visibility(data, "classified")


def test_filter_by_visibility_returns_values(data):
    """Ensure filter_by_visibility returns a mapping of key -> value, not just keys."""
    set_visibility(data, "DEBUG", "public")
    result = filter_by_visibility(data, "public")
    assert result.get("DEBUG") == "false"


def test_list_visibility_returns_explicit_entries(data):
    set_visibility(data, "API_KEY", "hidden")
    set_visibility(data, "DEBUG", "public")
    result = list_visibility(data)
    assert result == {"API_KEY": "hidden", "DEBUG": "public"}


def test_list_visibility_empty_when_none_set(data):
    assert list_visibility(data) == {}
