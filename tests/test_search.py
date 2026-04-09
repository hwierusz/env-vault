"""Tests for env_vault.search module."""

import json
import pytest

from unittest.mock import patch

from env_vault.search import search_vars, SearchError
from env_vault.crypto import encrypt


VAULT_NAME = "test_vault"
PASSWORD = "supersecret"

SAMPLE_VARS = {
    "DATABASE_URL": "postgres://localhost/mydb",
    "DATABASE_PASSWORD": "db_pass_123",
    "APP_SECRET_KEY": "abc123",
    "DEBUG": "true",
    "PORT": "8080",
}


@pytest.fixture
def mock_vault():
    """Patch load_vault to return an encrypted version of SAMPLE_VARS."""
    encrypted = encrypt(json.dumps(SAMPLE_VARS).encode(), PASSWORD)
    vault_data = {"data": encrypted}
    with patch("env_vault.search.load_vault", return_value=vault_data):
        yield


def test_search_by_key_prefix(mock_vault):
    results = search_vars(VAULT_NAME, PASSWORD, "^DATABASE")
    assert set(results.keys()) == {"DATABASE_URL", "DATABASE_PASSWORD"}


def test_search_case_insensitive_by_default(mock_vault):
    results = search_vars(VAULT_NAME, PASSWORD, "debug")
    assert "DEBUG" in results


def test_search_case_sensitive(mock_vault):
    results = search_vars(VAULT_NAME, PASSWORD, "debug", case_sensitive=True)
    assert "DEBUG" not in results


def test_search_returns_empty_when_no_match(mock_vault):
    results = search_vars(VAULT_NAME, PASSWORD, "NONEXISTENT")
    assert results == {}


def test_search_values(mock_vault):
    results = search_vars(VAULT_NAME, PASSWORD, "postgres", search_values=True)
    assert "DATABASE_URL" in results


def test_search_values_not_searched_by_default(mock_vault):
    results = search_vars(VAULT_NAME, PASSWORD, "postgres", search_values=False)
    assert results == {}


def test_search_invalid_pattern_raises(mock_vault):
    with pytest.raises(SearchError, match="Invalid pattern"):
        search_vars(VAULT_NAME, PASSWORD, "[invalid")


def test_search_missing_vault_raises():
    with patch("env_vault.search.load_vault", side_effect=FileNotFoundError):
        with pytest.raises(SearchError, match="does not exist"):
            search_vars(VAULT_NAME, PASSWORD, ".*")


def test_search_wrong_password_raises():
    encrypted = encrypt(json.dumps(SAMPLE_VARS).encode(), PASSWORD)
    vault_data = {"data": encrypted}
    with patch("env_vault.search.load_vault", return_value=vault_data):
        with pytest.raises(SearchError, match="Failed to decrypt"):
            search_vars(VAULT_NAME, "wrongpassword", ".*")
