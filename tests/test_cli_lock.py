"""Tests for env_vault.cli_lock."""

import pytest
from click.testing import CliRunner

from env_vault.cli_lock import lock_cmd
from env_vault.lock import lock_vault


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def patched(tmp_path, monkeypatch):
    """Redirect all lock operations to a temp directory."""
    import env_vault.lock as lock_mod
    import env_vault.cli_lock as cli_mod

    vault_dir = str(tmp_path)

    original_lock = lock_mod.lock_vault
    original_unlock = lock_mod.unlock_vault
    original_info = lock_mod.get_lock_info

    monkeypatch.setattr(cli_mod, "lock_vault", lambda n, reason="": original_lock(n, reason=reason, vault_dir=vault_dir))
    monkeypatch.setattr(cli_mod, "unlock_vault", lambda n: original_unlock(n, vault_dir=vault_dir))
    monkeypatch.setattr(cli_mod, "get_lock_info", lambda n: original_info(n, vault_dir=vault_dir))
    monkeypatch.setattr(cli_mod, "is_locked", lambda n: lock_mod.is_locked(n, vault_dir=vault_dir))

    return vault_dir


def test_lock_on_success(runner, patched):
    result = runner.invoke(lock_cmd, ["on", "myproject"])
    assert result.exit_code == 0
    assert "locked" in result.output


def test_lock_on_with_reason(runner, patched):
    result = runner.invoke(lock_cmd, ["on", "myproject", "--reason", "freeze"])
    assert result.exit_code == 0
    assert "freeze" in result.output


def test_lock_on_already_locked(runner, patched, tmp_path):
    import env_vault.lock as lock_mod
    lock_mod.lock_vault("myproject", vault_dir=patched)
    result = runner.invoke(lock_cmd, ["on", "myproject"])
    assert result.exit_code == 1
    assert "already locked" in result.output


def test_lock_off_success(runner, patched):
    import env_vault.lock as lock_mod
    lock_mod.lock_vault("myproject", vault_dir=patched)
    result = runner.invoke(lock_cmd, ["off", "myproject"])
    assert result.exit_code == 0
    assert "unlocked" in result.output


def test_lock_off_not_locked(runner, patched):
    result = runner.invoke(lock_cmd, ["off", "myproject"])
    assert result.exit_code == 1
    assert "not locked" in result.output


def test_lock_status_unlocked(runner, patched):
    result = runner.invoke(lock_cmd, ["status", "myproject"])
    assert result.exit_code == 0
    assert "unlocked" in result.output


def test_lock_status_locked(runner, patched):
    import env_vault.lock as lock_mod
    lock_mod.lock_vault("myproject", reason="testing", vault_dir=patched)
    result = runner.invoke(lock_cmd, ["status", "myproject"])
    assert result.exit_code == 0
    assert "LOCKED" in result.output
    assert "testing" in result.output
