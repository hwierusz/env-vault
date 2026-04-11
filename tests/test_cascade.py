"""Tests for env_vault.cascade module."""

import pytest
from unittest.mock import patch
from env_vault.cascade import CascadeError, resolve_cascade, cascade_sources


VAULT_A = {"vars": {"HOST": "localhost", "PORT": "5432", "DEBUG": "false"}}
VAULT_B = {"vars": {"PORT": "6543", "SECRET": "abc123"}}
VAULT_C = {"vars": {"DEBUG": "true", "SECRET": "xyz789"}}


def _make_loader(mapping):
    def _load(name, password, **kwargs):
        return mapping[name]
    return _load


def _exists(name, **kwargs):
    return True


def test_resolve_cascade_single_vault():
    loader = _make_loader({"base": VAULT_A})
    with patch("env_vault.cascade.vault_exists", _exists), \
         patch("env_vault.cascade.load_vault", loader):
        result = resolve_cascade(["base"], password="pw")
    assert result == {"HOST": "localhost", "PORT": "5432", "DEBUG": "false"}


def test_resolve_cascade_later_vault_wins():
    loader = _make_loader({"a": VAULT_A, "b": VAULT_B})
    with patch("env_vault.cascade.vault_exists", _exists), \
         patch("env_vault.cascade.load_vault", loader):
        result = resolve_cascade(["a", "b"], password="pw")
    assert result["PORT"] == "6543"   # b overrides a
    assert result["HOST"] == "localhost"  # only in a
    assert result["SECRET"] == "abc123"   # only in b


def test_resolve_cascade_three_vaults_priority():
    loader = _make_loader({"a": VAULT_A, "b": VAULT_B, "c": VAULT_C})
    with patch("env_vault.cascade.vault_exists", _exists), \
         patch("env_vault.cascade.load_vault", loader):
        result = resolve_cascade(["a", "b", "c"], password="pw")
    assert result["DEBUG"] == "true"     # c overrides a
    assert result["SECRET"] == "xyz789"  # c overrides b
    assert result["PORT"] == "6543"      # b overrides a, c doesn't have it


def test_resolve_cascade_empty_list_raises():
    with pytest.raises(CascadeError, match="At least one"):
        resolve_cascade([], password="pw")


def test_resolve_cascade_missing_vault_raises():
    def _missing(name, **kwargs):
        return name != "missing"

    with patch("env_vault.cascade.vault_exists", _missing):
        with pytest.raises(CascadeError, match="missing"):
            resolve_cascade(["missing"], password="pw")


def test_cascade_sources_single_vault():
    loader = _make_loader({"base": VAULT_A})
    with patch("env_vault.cascade.vault_exists", _exists), \
         patch("env_vault.cascade.load_vault", loader):
        sources = cascade_sources(["base"], password="pw")
    assert sources == {"HOST": "base", "PORT": "base", "DEBUG": "base"}


def test_cascade_sources_shows_last_definer():
    loader = _make_loader({"a": VAULT_A, "b": VAULT_B})
    with patch("env_vault.cascade.vault_exists", _exists), \
         patch("env_vault.cascade.load_vault", loader):
        sources = cascade_sources(["a", "b"], password="pw")
    assert sources["PORT"] == "b"
    assert sources["HOST"] == "a"
    assert sources["SECRET"] == "b"


def test_cascade_sources_empty_list_raises():
    with pytest.raises(CascadeError):
        cascade_sources([], password="pw")
