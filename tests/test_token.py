"""Tests for env_vault.token module."""
import time
import pytest
from env_vault.token import (
    TokenError,
    issue_token,
    revoke_token,
    resolve_token,
    list_tokens,
    purge_expired_tokens,
)


@pytest.fixture
def data():
    return {"DB_URL": "postgres://localhost", "API_KEY": "secret123", "HOST": "localhost"}


def test_issue_token_returns_hex_string(data):
    token = issue_token(data, "ci", ["DB_URL"])
    assert isinstance(token, str)
    assert len(token) == 64


def test_issue_token_stores_metadata(data):
    token = issue_token(data, "ci", ["DB_URL", "HOST"])
    tokens = data["__tokens__"]
    assert token in tokens
    assert tokens[token]["label"] == "ci"
    assert tokens[token]["allowed_keys"] == ["DB_URL", "HOST"]


def test_issue_token_missing_key_raises(data):
    with pytest.raises(TokenError, match="Key not found"):
        issue_token(data, "ci", ["MISSING_KEY"])


def test_issue_token_empty_keys_raises(data):
    with pytest.raises(TokenError, match="allowed_keys must not be empty"):
        issue_token(data, "ci", [])


def test_issue_token_non_positive_ttl_raises(data):
    with pytest.raises(TokenError, match="ttl_seconds must be positive"):
        issue_token(data, "ci", ["DB_URL"], ttl_seconds=0)


def test_resolve_token_returns_correct_values(data):
    token = issue_token(data, "ci", ["DB_URL"])
    result = resolve_token(data, token)
    assert result == {"DB_URL": "postgres://localhost"}


def test_resolve_token_not_found_raises(data):
    with pytest.raises(TokenError, match="Token not found"):
        resolve_token(data, "deadbeef" * 8)


def test_resolve_expired_token_raises(data):
    token = issue_token(data, "ci", ["DB_URL"], ttl_seconds=1)
    data["__tokens__"][token]["expires_at"] = time.time() - 1
    with pytest.raises(TokenError, match="expired"):
        resolve_token(data, token)


def test_revoke_token_removes_entry(data):
    token = issue_token(data, "ci", ["DB_URL"])
    revoke_token(data, token)
    assert token not in data["__tokens__"]


def test_revoke_missing_token_raises(data):
    with pytest.raises(TokenError, match="Token not found"):
        revoke_token(data, "notexist")


def test_list_tokens_returns_metadata(data):
    issue_token(data, "ci", ["DB_URL"])
    issue_token(data, "deploy", ["API_KEY"])
    tokens = list_tokens(data)
    assert len(tokens) == 2
    labels = {t["label"] for t in tokens}
    assert labels == {"ci", "deploy"}


def test_list_tokens_masks_token_value(data):
    issue_token(data, "ci", ["DB_URL"])
    tokens = list_tokens(data)
    assert tokens[0]["token"].endswith("...")


def test_purge_expired_tokens_removes_expired(data):
    token = issue_token(data, "ci", ["DB_URL"], ttl_seconds=1)
    data["__tokens__"][token]["expires_at"] = time.time() - 1
    count = purge_expired_tokens(data)
    assert count == 1
    assert token not in data["__tokens__"]


def test_purge_expired_tokens_keeps_valid(data):
    issue_token(data, "ci", ["DB_URL"], ttl_seconds=3600)
    count = purge_expired_tokens(data)
    assert count == 0
    assert len(data["__tokens__"]) == 1
