"""Tests for the storage module."""

import pytest
from pathlib import Path
from env_vault.storage import (
    save_vault, load_vault, vault_exists, list_vaults, delete_vault
)

PASSWORD = "vault-password"
PROJECT = "my-project"
VARIABLES = {"API_KEY": "secret123", "DEBUG": "true", "PORT": "8080"}


@pytest.fixture
def vault_dir(tmp_path):
    return tmp_path / "vaults"


def test_save_and_load_vault(vault_dir):
    save_vault(PROJECT, VARIABLES, PASSWORD, vault_dir)
    loaded = load_vault(PROJECT, PASSWORD, vault_dir)
    assert loaded == VARIABLES


def test_vault_file_created(vault_dir):
    path = save_vault(PROJECT, VARIABLES, PASSWORD, vault_dir)
    assert path.exists()
    assert path.suffix == ".vault"


def test_vault_exists_true(vault_dir):
    save_vault(PROJECT, VARIABLES, PASSWORD, vault_dir)
    assert vault_exists(PROJECT, vault_dir) is True


def test_vault_exists_false(vault_dir):
    assert vault_exists("nonexistent", vault_dir) is False


def test_load_nonexistent_vault_raises(vault_dir):
    with pytest.raises(FileNotFoundError, match="No vault found"):
        load_vault("ghost-project", PASSWORD, vault_dir)


def test_load_wrong_password_raises(vault_dir):
    save_vault(PROJECT, VARIABLES, PASSWORD, vault_dir)
    with pytest.raises(ValueError):
        load_vault(PROJECT, "wrong-password", vault_dir)


def test_list_vaults(vault_dir):
    save_vault("alpha", VARIABLES, PASSWORD, vault_dir)
    save_vault("beta", VARIABLES, PASSWORD, vault_dir)
    names = list_vaults(vault_dir)
    assert "alpha" in names
    assert "beta" in names


def test_list_vaults_empty(vault_dir):
    assert list_vaults(vault_dir) == []


def test_delete_vault(vault_dir):
    save_vault(PROJECT, VARIABLES, PASSWORD, vault_dir)
    assert delete_vault(PROJECT, vault_dir) is True
    assert vault_exists(PROJECT, vault_dir) is False


def test_delete_nonexistent_vault(vault_dir):
    assert delete_vault("ghost", vault_dir) is False
