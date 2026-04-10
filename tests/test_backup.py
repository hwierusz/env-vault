"""Tests for env_vault.backup."""

import os
import pytest

from env_vault.backup import BackupError, create_backup, restore_backup
from env_vault.storage import save_vault, load_vault


PASSWORD = "s3cr3t"
VAULT = "backup_test_vault"
VARS = {"DB_HOST": "localhost", "API_KEY": "abc123"}


@pytest.fixture()
def vault_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("ENV_VAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def seeded_vault(vault_dir):
    save_vault(VAULT, PASSWORD, VARS)
    return vault_dir


def test_create_backup_returns_path(seeded_vault, tmp_path):
    dest = str(tmp_path / "my.bak")
    path = create_backup(VAULT, PASSWORD, dest)
    assert path == dest


def test_backup_file_is_created(seeded_vault, tmp_path):
    dest = str(tmp_path / "my.bak")
    create_backup(VAULT, PASSWORD, dest)
    assert os.path.isfile(dest)


def test_backup_file_is_binary(seeded_vault, tmp_path):
    dest = str(tmp_path / "my.bak")
    create_backup(VAULT, PASSWORD, dest)
    with open(dest, "rb") as fh:
        data = fh.read()
    assert isinstance(data, bytes)
    assert len(data) > 0


def test_restore_roundtrip(seeded_vault, tmp_path):
    dest = str(tmp_path / "my.bak")
    create_backup(VAULT, PASSWORD, dest)
    target = restore_backup(dest, PASSWORD)
    result = load_vault(target, PASSWORD)
    assert result == VARS


def test_restore_into_new_vault_name(seeded_vault, tmp_path):
    dest = str(tmp_path / "my.bak")
    create_backup(VAULT, PASSWORD, dest)
    target = restore_backup(dest, PASSWORD, vault_name="new_vault")
    assert target == "new_vault"
    result = load_vault("new_vault", PASSWORD)
    assert result == VARS


def test_create_backup_missing_vault_raises(vault_dir, tmp_path):
    with pytest.raises(BackupError, match="does not exist"):
        create_backup("nonexistent", PASSWORD, str(tmp_path / "x.bak"))


def test_restore_missing_file_raises(vault_dir, tmp_path):
    with pytest.raises(BackupError, match="not found"):
        restore_backup(str(tmp_path / "ghost.bak"), PASSWORD)


def test_restore_wrong_password_raises(seeded_vault, tmp_path):
    dest = str(tmp_path / "my.bak")
    create_backup(VAULT, PASSWORD, dest)
    with pytest.raises(BackupError, match="wrong password"):
        restore_backup(dest, "wrongpassword")
