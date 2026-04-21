"""Tests for env_vault.inherit."""
from __future__ import annotations

from typing import Dict

import pytest

from env_vault.inherit import InheritError, InheritResult, inherit_all, resolve_inherited


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_loader(vaults: Dict[str, Dict[str, str]]):
    def _load(name: str, _password: str) -> Dict[str, str]:
        return vaults[name]
    return _load


def _make_exists(vaults: Dict[str, Dict[str, str]]):
    def _exists(name: str) -> bool:
        return name in vaults
    return _exists


# ---------------------------------------------------------------------------
# resolve_inherited
# ---------------------------------------------------------------------------

def test_resolve_finds_key_in_first_vault():
    vaults = {"child": {"FOO": "bar"}, "parent": {"FOO": "baz"}}
    result = resolve_inherited(
        "FOO", ["child", "parent"],
        _make_loader(vaults), _make_exists(vaults), "pw"
    )
    assert result.value == "bar"
    assert result.source_vault == "child"
    assert result.depth == 0


def test_resolve_falls_through_to_parent():
    vaults = {"child": {}, "parent": {"FOO": "from_parent"}}
    result = resolve_inherited(
        "FOO", ["child", "parent"],
        _make_loader(vaults), _make_exists(vaults), "pw"
    )
    assert result.value == "from_parent"
    assert result.source_vault == "parent"
    assert result.depth == 1


def test_resolve_raises_when_key_missing_in_all_vaults():
    vaults = {"child": {}, "parent": {}}
    with pytest.raises(InheritError, match="FOO"):
        resolve_inherited(
            "FOO", ["child", "parent"],
            _make_loader(vaults), _make_exists(vaults), "pw"
        )


def test_resolve_raises_for_missing_vault():
    vaults = {"child": {"FOO": "v"}}
    with pytest.raises(InheritError, match="ghost"):
        resolve_inherited(
            "FOO", ["child", "ghost"],
            _make_loader(vaults), _make_exists(vaults), "pw"
        )


def test_resolve_raises_for_empty_vault_list():
    with pytest.raises(InheritError):
        resolve_inherited("FOO", [], lambda n, p: {}, lambda n: True, "pw")


def test_resolve_returns_inherit_result_instance():
    vaults = {"v": {"X": "1"}}
    result = resolve_inherited(
        "X", ["v"], _make_loader(vaults), _make_exists(vaults), "pw"
    )
    assert isinstance(result, InheritResult)


# ---------------------------------------------------------------------------
# inherit_all
# ---------------------------------------------------------------------------

def test_inherit_all_child_shadows_parent():
    vaults = {"child": {"A": "child_a"}, "parent": {"A": "parent_a", "B": "parent_b"}}
    merged = inherit_all(
        ["child", "parent"], _make_loader(vaults), _make_exists(vaults), "pw"
    )
    assert merged["A"].value == "child_a"
    assert merged["A"].source_vault == "child"
    assert merged["B"].value == "parent_b"
    assert merged["B"].source_vault == "parent"


def test_inherit_all_returns_all_keys():
    vaults = {"a": {"X": "1"}, "b": {"Y": "2"}, "c": {"Z": "3"}}
    merged = inherit_all(
        ["a", "b", "c"], _make_loader(vaults), _make_exists(vaults), "pw"
    )
    assert set(merged.keys()) == {"X", "Y", "Z"}


def test_inherit_all_raises_for_missing_vault():
    vaults = {"real": {"K": "v"}}
    with pytest.raises(InheritError, match="missing"):
        inherit_all(
            ["real", "missing"], _make_loader(vaults), _make_exists(vaults), "pw"
        )


def test_inherit_all_raises_for_empty_list():
    with pytest.raises(InheritError):
        inherit_all([], lambda n, p: {}, lambda n: True, "pw")


def test_inherit_all_depth_reflects_position():
    vaults = {"a": {}, "b": {}, "c": {"ONLY": "here"}}
    merged = inherit_all(
        ["a", "b", "c"], _make_loader(vaults), _make_exists(vaults), "pw"
    )
    assert merged["ONLY"].depth == 2
