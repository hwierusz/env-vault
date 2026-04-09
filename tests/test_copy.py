"""Tests for env_vault.copy module."""

import pytest
from unittest.mock import patch, MagicMock
from env_vault.copy import copy_vars, CopyError


SRC = "src_vault"
DST = "dst_vault"
SRC_PASS = "src_pass"
DST_PASS = "dst_pass"
SRC_DATA = {"API_KEY": "abc123", "DB_URL": "postgres://localhost"}
DST_DATA = {"EXISTING": "value"}


def _make_load(src_data, dst_data):
    def _load(vault, password):
        return dict(src_data) if vault == SRC else dict(dst_data)
    return _load


@patch("env_vault.copy.record_event")
@patch("env_vault.copy.save_vault")
@patch("env_vault.copy.load_vault")
@patch("env_vault.copy.vault_exists", return_value=True)
def test_copy_all_vars(mock_exists, mock_load, mock_save, mock_audit):
    mock_load.side_effect = _make_load(SRC_DATA, DST_DATA)
    count = copy_vars(SRC, DST, SRC_PASS, DST_PASS)
    assert count == len(SRC_DATA)
    saved = mock_save.call_args[0][2]
    assert "API_KEY" in saved
    assert "DB_URL" in saved
    assert "EXISTING" in saved


@patch("env_vault.copy.record_event")
@patch("env_vault.copy.save_vault")
@patch("env_vault.copy.load_vault")
@patch("env_vault.copy.vault_exists", return_value=True)
def test_copy_specific_keys(mock_exists, mock_load, mock_save, mock_audit):
    mock_load.side_effect = _make_load(SRC_DATA, DST_DATA)
    count = copy_vars(SRC, DST, SRC_PASS, DST_PASS, keys=["API_KEY"])
    assert count == 1
    saved = mock_save.call_args[0][2]
    assert "API_KEY" in saved
    assert "DB_URL" not in saved


@patch("env_vault.copy.vault_exists", side_effect=[False, True])
def test_copy_raises_if_src_missing(mock_exists):
    with pytest.raises(CopyError, match="Source vault"):
        copy_vars(SRC, DST, SRC_PASS, DST_PASS)


@patch("env_vault.copy.vault_exists", side_effect=[True, False])
def test_copy_raises_if_dst_missing(mock_exists):
    with pytest.raises(CopyError, match="Destination vault"):
        copy_vars(SRC, DST, SRC_PASS, DST_PASS)


@patch("env_vault.copy.load_vault")
@patch("env_vault.copy.vault_exists", return_value=True)
def test_copy_raises_on_conflict_without_overwrite(mock_exists, mock_load):
    conflicting_dst = {"API_KEY": "old_value"}
    mock_load.side_effect = _make_load(SRC_DATA, conflicting_dst)
    with pytest.raises(CopyError, match="Key conflict"):
        copy_vars(SRC, DST, SRC_PASS, DST_PASS, overwrite=False)


@patch("env_vault.copy.record_event")
@patch("env_vault.copy.save_vault")
@patch("env_vault.copy.load_vault")
@patch("env_vault.copy.vault_exists", return_value=True)
def test_copy_overwrite_replaces_existing(mock_exists, mock_load, mock_save, mock_audit):
    conflicting_dst = {"API_KEY": "old_value"}
    mock_load.side_effect = _make_load(SRC_DATA, conflicting_dst)
    count = copy_vars(SRC, DST, SRC_PASS, DST_PASS, overwrite=True)
    assert count == len(SRC_DATA)
    saved = mock_save.call_args[0][2]
    assert saved["API_KEY"] == "abc123"


@patch("env_vault.copy.record_event")
@patch("env_vault.copy.save_vault")
@patch("env_vault.copy.load_vault")
@patch("env_vault.copy.vault_exists", return_value=True)
def test_copy_records_audit_events(mock_exists, mock_load, mock_save, mock_audit):
    mock_load.side_effect = _make_load(SRC_DATA, DST_DATA)
    copy_vars(SRC, DST, SRC_PASS, DST_PASS)
    assert mock_audit.call_count == len(SRC_DATA)
    calls = [c[0] for c in mock_audit.call_args_list]
    actions = [c[1] for c in calls]
    assert all(a == "copy" for a in actions)
