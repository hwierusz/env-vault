"""Tests for env_vault.cli_backup."""

import os
import pytest
from click.testing import CliRunner

from env_vault.cli_backup import backup_cmd
from env_vault.storage import save_vault


PASSWORD = "s3cr3t"
VAULT = "cli_backup_vault"
VARS = {"FOO": "bar", "BAZ": "qux"}


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def seeded(tmp_path, monkeypatch):
    monkeypatch.setenv("ENV_VAULT_DIR", str(tmp_path))
    save_vault(VAULT, PASSWORD, VARS)
    return tmp_path


def test_backup_create_success(runner, seeded, tmp_path):
    dest = str(tmp_path / "out.bak")
    result = runner.invoke(
        backup_cmd, ["create", VAULT, dest, "--password", PASSWORD]
    )
    assert result.exit_code == 0
    assert "Backup written to" in result.output
    assert os.path.isfile(dest)


def test_backup_create_missing_vault(runner, seeded, tmp_path):
    dest = str(tmp_path / "out.bak")
    result = runner.invoke(
        backup_cmd, ["create", "ghost", dest, "--password", PASSWORD]
    )
    assert result.exit_code != 0
    assert "Error" in result.output


def test_backup_restore_success(runner, seeded, tmp_path):
    dest = str(tmp_path / "out.bak")
    runner.invoke(backup_cmd, ["create", VAULT, dest, "--password", PASSWORD])
    result = runner.invoke(
        backup_cmd, ["restore", dest, "--password", PASSWORD]
    )
    assert result.exit_code == 0
    assert "Restored into vault" in result.output


def test_backup_restore_override_name(runner, seeded, tmp_path):
    dest = str(tmp_path / "out.bak")
    runner.invoke(backup_cmd, ["create", VAULT, dest, "--password", PASSWORD])
    result = runner.invoke(
        backup_cmd, ["restore", dest, "--vault", "renamed", "--password", PASSWORD]
    )
    assert result.exit_code == 0
    assert "renamed" in result.output


def test_backup_restore_wrong_password(runner, seeded, tmp_path):
    dest = str(tmp_path / "out.bak")
    runner.invoke(backup_cmd, ["create", VAULT, dest, "--password", PASSWORD])
    result = runner.invoke(
        backup_cmd, ["restore", dest, "--password", "badpass"]
    )
    assert result.exit_code != 0
    assert "Error" in result.output
