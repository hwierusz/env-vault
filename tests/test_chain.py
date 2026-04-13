"""Tests for env_vault.chain."""

from __future__ import annotations

import pytest

from env_vault.chain import ChainError, ChainResult, chain_sources, resolve_chain


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

VAULT_A = {"KEY1": "alpha", "SHARED": "from_a"}
VAULT_B = {"KEY2": "beta", "SHARED": "from_b"}
VAULT_C = {"KEY3": "gamma"}

_DATA = {"a": VAULT_A, "b": VAULT_B, "c": VAULT_C}


def _load(name: str):
    return _DATA[name]


def _exists(name: str) -> bool:
    return name in _DATA


# ---------------------------------------------------------------------------
# resolve_chain
# ---------------------------------------------------------------------------

def test_resolve_chain_finds_key_in_first_vault():
    result = resolve_chain("KEY1", ["a", "b"], _load, _exists)
    assert isinstance(result, ChainResult)
    assert result.key == "KEY1"
    assert result.value == "alpha"
    assert result.source == "a"


def test_resolve_chain_falls_through_to_second_vault():
    result = resolve_chain("KEY2", ["a", "b"], _load, _exists)
    assert result.value == "beta"
    assert result.source == "b"


def test_resolve_chain_first_wins_for_shared_key():
    result = resolve_chain("SHARED", ["a", "b"], _load, _exists)
    assert result.value == "from_a"
    assert result.source == "a"


def test_resolve_chain_raises_when_key_missing_everywhere():
    with pytest.raises(ChainError, match="not found in any"):
        resolve_chain("MISSING", ["a", "b"], _load, _exists)


def test_resolve_chain_raises_on_unknown_vault():
    with pytest.raises(ChainError, match="vault not found"):
        resolve_chain("KEY1", ["a", "unknown"], _load, _exists)


def test_resolve_chain_raises_on_empty_vault_list():
    with pytest.raises(ChainError, match="must not be empty"):
        resolve_chain("KEY1", [], _load, _exists)


# ---------------------------------------------------------------------------
# chain_sources
# ---------------------------------------------------------------------------

def test_chain_sources_merges_all_vaults():
    merged = chain_sources(["a", "b", "c"], _load, _exists)
    assert "KEY1" in merged
    assert "KEY2" in merged
    assert "KEY3" in merged


def test_chain_sources_first_wins():
    merged = chain_sources(["a", "b"], _load, _exists)
    assert merged["SHARED"] == "from_a"


def test_chain_sources_later_wins_when_reversed():
    merged = chain_sources(["b", "a"], _load, _exists)
    assert merged["SHARED"] == "from_b"


def test_chain_sources_raises_on_empty_list():
    with pytest.raises(ChainError, match="must not be empty"):
        chain_sources([], _load, _exists)


def test_chain_sources_raises_on_unknown_vault():
    with pytest.raises(ChainError, match="vault not found"):
        chain_sources(["a", "nope"], _load, _exists)
