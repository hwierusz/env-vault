"""Tests for env_vault.observe."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from env_vault.observe import (
    ObserveError,
    clear_observations,
    read_observations,
    record_read,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


VAULT = "myvault"


def test_record_read_creates_log_file(vault_dir: Path) -> None:
    record_read(VAULT, "API_KEY", actor="alice", vault_dir=vault_dir)
    log_files = list(vault_dir.glob("*.observe_log"))
    assert len(log_files) == 1


def test_record_read_writes_valid_json(vault_dir: Path) -> None:
    before = time.time()
    record_read(VAULT, "DB_URL", actor="bob", vault_dir=vault_dir)
    after = time.time()

    events = read_observations(VAULT, vault_dir=vault_dir)
    assert len(events) == 1
    ev = events[0]
    assert ev["key"] == "DB_URL"
    assert ev["actor"] == "bob"
    assert ev["vault"] == VAULT
    assert before <= ev["ts"] <= after


def test_multiple_reads_appended(vault_dir: Path) -> None:
    record_read(VAULT, "KEY_A", vault_dir=vault_dir)
    record_read(VAULT, "KEY_B", vault_dir=vault_dir)
    record_read(VAULT, "KEY_A", vault_dir=vault_dir)

    events = read_observations(VAULT, vault_dir=vault_dir)
    assert len(events) == 3


def test_filter_by_key(vault_dir: Path) -> None:
    record_read(VAULT, "KEY_A", vault_dir=vault_dir)
    record_read(VAULT, "KEY_B", vault_dir=vault_dir)

    filtered = read_observations(VAULT, vault_dir=vault_dir, key="KEY_A")
    assert len(filtered) == 1
    assert filtered[0]["key"] == "KEY_A"


def test_read_observations_returns_empty_when_no_log(vault_dir: Path) -> None:
    events = read_observations("nonexistent", vault_dir=vault_dir)
    assert events == []


def test_clear_observations_returns_count(vault_dir: Path) -> None:
    record_read(VAULT, "KEY_A", vault_dir=vault_dir)
    record_read(VAULT, "KEY_B", vault_dir=vault_dir)

    removed = clear_observations(VAULT, vault_dir=vault_dir)
    assert removed == 2


def test_clear_observations_removes_file(vault_dir: Path) -> None:
    record_read(VAULT, "KEY_A", vault_dir=vault_dir)
    clear_observations(VAULT, vault_dir=vault_dir)

    events = read_observations(VAULT, vault_dir=vault_dir)
    assert events == []


def test_clear_observations_on_missing_log_returns_zero(vault_dir: Path) -> None:
    result = clear_observations("ghost_vault", vault_dir=vault_dir)
    assert result == 0


def test_corrupt_log_raises_observe_error(vault_dir: Path) -> None:
    log_path = vault_dir / f"{VAULT}.observe_log"
    log_path.write_text("not-json\n", encoding="utf-8")

    with pytest.raises(ObserveError, match="Corrupt"):
        read_observations(VAULT, vault_dir=vault_dir)


def test_default_actor_is_unknown(vault_dir: Path) -> None:
    record_read(VAULT, "SECRET", vault_dir=vault_dir)
    events = read_observations(VAULT, vault_dir=vault_dir)
    assert events[0]["actor"] == "unknown"
