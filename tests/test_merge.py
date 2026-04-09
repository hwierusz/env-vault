"""Tests for env_vault.merge module."""

import pytest
from unittest.mock import patch, MagicMock
from env_vault.merge import merge_vaults, MergeError


PASSWORD = "test-pass"


def _make_loader(vaults: dict):
    """Return a load_vault side_effect that reads from an in-memory dict."""
    def _load(name, password):
        return dict(vaults[name])
    return _load


def _make_saver(store: dict):
    def _save(name, password, data):
        store[name] = dict(data)
    return _save


@pytest.fixture()
def two_vaults():
    return {
        "src": {"FOO": "foo_val", "BAR": "bar_val"},
        "dst": {"BAZ": "baz_val"},
    }


def test_merge_adds_all_vars(two_vaults):
    saved = {}
    with patch("env_vault.merge.vault_exists", return_value=True), \
         patch("env_vault.merge.load_vault", side_effect=_make_loader(two_vaults)), \
         patch("env_vault.merge.save_vault", side_effect=_make_saver(saved)), \
         patch("env_vault.merge.record_event"):
        result = merge_vaults("src", PASSWORD, "dst", PASSWORD)
    assert set(result["added"]) == {"FOO", "BAR"}
    assert result["skipped"] == []
    assert saved["dst"]["FOO"] == "foo_val"
    assert saved["dst"]["BAZ"] == "baz_val"


def test_merge_skips_existing_by_default(two_vaults):
    two_vaults["dst"]["FOO"] = "original"
    saved = {}
    with patch("env_vault.merge.vault_exists", return_value=True), \
         patch("env_vault.merge.load_vault", side_effect=_make_loader(two_vaults)), \
         patch("env_vault.merge.save_vault", side_effect=_make_saver(saved)), \
         patch("env_vault.merge.record_event"):
        result = merge_vaults("src", PASSWORD, "dst", PASSWORD)
    assert "FOO" in result["skipped"]
    assert saved["dst"]["FOO"] == "original"


def test_merge_overwrite_replaces_existing(two_vaults):
    two_vaults["dst"]["FOO"] = "original"
    saved = {}
    with patch("env_vault.merge.vault_exists", return_value=True), \
         patch("env_vault.merge.load_vault", side_effect=_make_loader(two_vaults)), \
         patch("env_vault.merge.save_vault", side_effect=_make_saver(saved)), \
         patch("env_vault.merge.record_event"):
        result = merge_vaults("src", PASSWORD, "dst", PASSWORD, overwrite=True)
    assert "FOO" in result["added"]
    assert saved["dst"]["FOO"] == "foo_val"


def test_merge_specific_keys_only(two_vaults):
    saved = {}
    with patch("env_vault.merge.vault_exists", return_value=True), \
         patch("env_vault.merge.load_vault", side_effect=_make_loader(two_vaults)), \
         patch("env_vault.merge.save_vault", side_effect=_make_saver(saved)), \
         patch("env_vault.merge.record_event"):
        result = merge_vaults("src", PASSWORD, "dst", PASSWORD, keys=["FOO"])
    assert result["added"] == ["FOO"]
    assert "BAR" not in saved["dst"]


def test_merge_raises_if_src_missing():
    def exists(name):
        return name != "src"
    with patch("env_vault.merge.vault_exists", side_effect=exists):
        with pytest.raises(MergeError, match="Source vault"):
            merge_vaults("src", PASSWORD, "dst", PASSWORD)


def test_merge_raises_if_dst_missing():
    def exists(name):
        return name != "dst"
    with patch("env_vault.merge.vault_exists", side_effect=exists):
        with pytest.raises(MergeError, match="Destination vault"):
            merge_vaults("src", PASSWORD, "dst", PASSWORD)


def test_merge_raises_on_bad_src_password(two_vaults):
    def bad_load(name, password):
        if name == "src":
            raise ValueError("bad password")
        return two_vaults[name]
    with patch("env_vault.merge.vault_exists", return_value=True), \
         patch("env_vault.merge.load_vault", side_effect=bad_load):
        with pytest.raises(MergeError, match="Failed to load source"):
            merge_vaults("src", "wrong", "dst", PASSWORD)
