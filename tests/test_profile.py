"""Tests for env_vault.profile."""

import pytest

from env_vault.profile import (
    ProfileError,
    delete_profile,
    get_profile,
    get_profile_var,
    list_profiles,
    set_profile_var,
)


PASSWORD = "test-password"
VAULT = "test_profile_vault"


@pytest.fixture(autouse=True)
def vault_dir(tmp_path, monkeypatch):
    import env_vault.storage as storage

    monkeypatch.setattr(storage, "VAULT_DIR", str(tmp_path))
    from env_vault.storage import save_vault

    save_vault(VAULT, PASSWORD, {})
    return tmp_path


def test_list_profiles_empty():
    assert list_profiles(VAULT, PASSWORD) == []


def test_set_and_list_profiles():
    set_profile_var(VAULT, PASSWORD, "dev", "HOST", "localhost")
    set_profile_var(VAULT, PASSWORD, "prod", "HOST", "example.com")
    profiles = list_profiles(VAULT, PASSWORD)
    assert profiles == ["dev", "prod"]


def test_get_profile_var_returns_value():
    set_profile_var(VAULT, PASSWORD, "dev", "PORT", "5432")
    assert get_profile_var(VAULT, PASSWORD, "dev", "PORT") == "5432"


def test_get_profile_var_missing_returns_none():
    set_profile_var(VAULT, PASSWORD, "dev", "PORT", "5432")
    assert get_profile_var(VAULT, PASSWORD, "dev", "MISSING") is None


def test_get_profile_var_unknown_profile_returns_none():
    assert get_profile_var(VAULT, PASSWORD, "nonexistent", "KEY") is None


def test_get_profile_returns_all_vars():
    set_profile_var(VAULT, PASSWORD, "staging", "A", "1")
    set_profile_var(VAULT, PASSWORD, "staging", "B", "2")
    result = get_profile(VAULT, PASSWORD, "staging")
    assert result == {"A": "1", "B": "2"}


def test_get_profile_raises_for_unknown_profile():
    with pytest.raises(ProfileError, match="does not exist"):
        get_profile(VAULT, PASSWORD, "ghost")


def test_set_profile_var_empty_name_raises():
    with pytest.raises(ProfileError, match="empty"):
        set_profile_var(VAULT, PASSWORD, "", "KEY", "val")


def test_delete_profile_returns_var_count():
    set_profile_var(VAULT, PASSWORD, "dev", "X", "1")
    set_profile_var(VAULT, PASSWORD, "dev", "Y", "2")
    count = delete_profile(VAULT, PASSWORD, "dev")
    assert count == 2


def test_delete_profile_removes_profile():
    set_profile_var(VAULT, PASSWORD, "dev", "X", "1")
    delete_profile(VAULT, PASSWORD, "dev")
    assert "dev" not in list_profiles(VAULT, PASSWORD)


def test_delete_nonexistent_profile_raises():
    with pytest.raises(ProfileError, match="does not exist"):
        delete_profile(VAULT, PASSWORD, "ghost")


def test_profiles_are_isolated():
    set_profile_var(VAULT, PASSWORD, "dev", "DB", "dev_db")
    set_profile_var(VAULT, PASSWORD, "prod", "DB", "prod_db")
    assert get_profile_var(VAULT, PASSWORD, "dev", "DB") == "dev_db"
    assert get_profile_var(VAULT, PASSWORD, "prod", "DB") == "prod_db"
