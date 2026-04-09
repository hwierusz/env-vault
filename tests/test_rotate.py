"""Tests for env_vault.rotate — password rotation."""

import pytest
from env_vault.rotate import rotate_password, RotationError
from env_vault.storage import save_vault, load_vault


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture()
def seeded_vault(vault_dir):
    """Create a vault with a known password and two variables."""
    data = {"API_KEY": "secret123", "DB_URL": "postgres://localhost/db"}
    save_vault("myproject", data, "old-pass", vault_dir=vault_dir)
    return vault_dir


def test_rotate_returns_variable_count(seeded_vault):
    count = rotate_password(
        "myproject", "old-pass", "new-pass", vault_dir=seeded_vault
    )
    assert count == 2


def test_rotated_vault_readable_with_new_password(seeded_vault):
    rotate_password("myproject", "old-pass", "new-pass", vault_dir=seeded_vault)
    data = load_vault("myproject", "new-pass", vault_dir=seeded_vault)
    assert data["API_KEY"] == "secret123"
    assert data["DB_URL"] == "postgres://localhost/db"


def test_old_password_no_longer_works(seeded_vault):
    rotate_password("myproject", "old-pass", "new-pass", vault_dir=seeded_vault)
    with pytest.raises(Exception):
        load_vault("myproject", "old-pass", vault_dir=seeded_vault)


def test_rotate_nonexistent_vault_raises(vault_dir):
    with pytest.raises(RotationError, match="does not exist"):
        rotate_password("ghost", "old-pass", "new-pass", vault_dir=vault_dir)


def test_rotate_wrong_old_password_raises(seeded_vault):
    with pytest.raises(RotationError, match="old password"):
        rotate_password(
            "myproject", "wrong-pass", "new-pass", vault_dir=seeded_vault
        )


def test_rotate_empty_vault(vault_dir):
    save_vault("empty", {}, "old-pass", vault_dir=vault_dir)
    count = rotate_password("empty", "old-pass", "new-pass", vault_dir=vault_dir)
    assert count == 0
    assert load_vault("empty", "new-pass", vault_dir=vault_dir) == {}


def test_rotate_records_audit_event(seeded_vault):
    from env_vault.audit import read_events

    rotate_password("myproject", "old-pass", "new-pass", vault_dir=seeded_vault)
    events = read_events("myproject", vault_dir=seeded_vault)
    actions = [e["action"] for e in events]
    assert "rotate_password" in actions
