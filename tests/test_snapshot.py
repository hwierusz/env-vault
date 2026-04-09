"""Tests for env_vault.snapshot."""

import json
import pytest
from pathlib import Path

from env_vault.snapshot import (
    SnapshotError,
    create_snapshot,
    list_snapshots,
    restore_snapshot,
)
from env_vault.storage import save_vault, load_vault

PASSWORD = "s3cret"


@pytest.fixture()
def vault_dir(tmp_path):
    return tmp_path


@pytest.fixture()
def seeded_vault(vault_dir):
    save_vault("myapp", PASSWORD, {"KEY1": "alpha", "KEY2": "beta"}, vault_dir=vault_dir)
    return vault_dir


def test_create_snapshot_returns_string_id(seeded_vault):
    sid = create_snapshot("myapp", PASSWORD, vault_dir=seeded_vault)
    assert isinstance(sid, str) and len(sid) > 0


def test_snapshot_file_written(seeded_vault):
    sid = create_snapshot("myapp", PASSWORD, vault_dir=seeded_vault)
    snap_file = seeded_vault / ".snapshots" / "myapp" / f"{sid}.json"
    assert snap_file.exists()


def test_snapshot_contains_vars(seeded_vault):
    sid = create_snapshot("myapp", PASSWORD, vault_dir=seeded_vault)
    snap_file = seeded_vault / ".snapshots" / "myapp" / f"{sid}.json"
    meta = json.loads(snap_file.read_text())
    assert meta["vars"] == {"KEY1": "alpha", "KEY2": "beta"}


def test_create_snapshot_with_label(seeded_vault):
    sid = create_snapshot("myapp", PASSWORD, label="before-deploy", vault_dir=seeded_vault)
    snap_file = seeded_vault / ".snapshots" / "myapp" / f"{sid}.json"
    meta = json.loads(snap_file.read_text())
    assert meta["label"] == "before-deploy"


def test_create_snapshot_missing_vault_raises(vault_dir):
    with pytest.raises(SnapshotError, match="does not exist"):
        create_snapshot("ghost", PASSWORD, vault_dir=vault_dir)


def test_list_snapshots_returns_metadata(seeded_vault):
    create_snapshot("myapp", PASSWORD, label="v1", vault_dir=seeded_vault)
    create_snapshot("myapp", PASSWORD, label="v2", vault_dir=seeded_vault)
    snaps = list_snapshots("myapp", vault_dir=seeded_vault)
    assert len(snaps) == 2
    assert all("vars" not in s for s in snaps)
    assert snaps[0]["label"] == "v1"
    assert snaps[1]["label"] == "v2"


def test_list_snapshots_empty(vault_dir):
    snaps = list_snapshots("nonexistent", vault_dir=vault_dir)
    assert snaps == []


def test_restore_snapshot_overwrites_vault(seeded_vault):
    sid = create_snapshot("myapp", PASSWORD, vault_dir=seeded_vault)
    # mutate vault after snapshot
    save_vault("myapp", PASSWORD, {"KEY1": "changed", "KEY3": "new"}, vault_dir=seeded_vault)
    count = restore_snapshot("myapp", sid, PASSWORD, vault_dir=seeded_vault)
    assert count == 2
    data = load_vault("myapp", PASSWORD, vault_dir=seeded_vault)
    assert data == {"KEY1": "alpha", "KEY2": "beta"}


def test_restore_missing_snapshot_raises(seeded_vault):
    with pytest.raises(SnapshotError, match="not found"):
        restore_snapshot("myapp", "0000000000000", PASSWORD, vault_dir=seeded_vault)
