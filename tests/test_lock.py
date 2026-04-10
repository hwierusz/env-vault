"""Tests for env_vault.lock."""

import pytest

from env_vault.lock import (
    LockError,
    _lock_path,
    assert_unlocked,
    get_lock_info,
    is_locked,
    lock_vault,
    unlock_vault,
)


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


def test_lock_creates_file(vault_dir):
    lock_vault("myproject", vault_dir=vault_dir)
    lp = _lock_path("myproject", vault_dir)
    assert lp.exists()


def test_is_locked_true_after_lock(vault_dir):
    lock_vault("myproject", vault_dir=vault_dir)
    assert is_locked("myproject", vault_dir=vault_dir) is True


def test_is_locked_false_before_lock(vault_dir):
    assert is_locked("myproject", vault_dir=vault_dir) is False


def test_lock_stores_reason(vault_dir):
    lock_vault("myproject", reason="maintenance", vault_dir=vault_dir)
    info = get_lock_info("myproject", vault_dir=vault_dir)
    assert info["reason"] == "maintenance"


def test_lock_stores_vault_name(vault_dir):
    lock_vault("myproject", vault_dir=vault_dir)
    info = get_lock_info("myproject", vault_dir=vault_dir)
    assert info["vault"] == "myproject"


def test_lock_stores_timestamp(vault_dir):
    import time

    before = time.time()
    lock_vault("myproject", vault_dir=vault_dir)
    after = time.time()
    info = get_lock_info("myproject", vault_dir=vault_dir)
    assert before <= info["locked_at"] <= after


def test_double_lock_raises(vault_dir):
    lock_vault("myproject", vault_dir=vault_dir)
    with pytest.raises(LockError, match="already locked"):
        lock_vault("myproject", vault_dir=vault_dir)


def test_unlock_removes_file(vault_dir):
    lock_vault("myproject", vault_dir=vault_dir)
    unlock_vault("myproject", vault_dir=vault_dir)
    assert not is_locked("myproject", vault_dir=vault_dir)


def test_unlock_when_not_locked_raises(vault_dir):
    with pytest.raises(LockError, match="not locked"):
        unlock_vault("myproject", vault_dir=vault_dir)


def test_get_lock_info_returns_none_when_unlocked(vault_dir):
    assert get_lock_info("myproject", vault_dir=vault_dir) is None


def test_assert_unlocked_passes_when_not_locked(vault_dir):
    assert_unlocked("myproject", vault_dir=vault_dir)  # should not raise


def test_assert_unlocked_raises_when_locked(vault_dir):
    lock_vault("myproject", reason="deploy freeze", vault_dir=vault_dir)
    with pytest.raises(LockError, match="deploy freeze"):
        assert_unlocked("myproject", vault_dir=vault_dir)
