"""Snapshot support: save and restore point-in-time copies of a vault."""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from env_vault.storage import load_vault, save_vault, vault_exists


class SnapshotError(Exception):
    pass


def _snapshot_dir(vault_dir: Path, vault_name: str) -> Path:
    d = vault_dir / ".snapshots" / vault_name
    d.mkdir(parents=True, exist_ok=True)
    return d


def create_snapshot(
    vault_name: str,
    password: str,
    label: Optional[str] = None,
    *,
    vault_dir: Optional[Path] = None,
) -> str:
    """Create a snapshot of *vault_name* and return its snapshot ID."""
    if not vault_exists(vault_name, vault_dir=vault_dir):
        raise SnapshotError(f"Vault '{vault_name}' does not exist.")

    data = load_vault(vault_name, password, vault_dir=vault_dir)
    snapshot_id = f"{int(time.time() * 1000)}"
    meta = {
        "id": snapshot_id,
        "vault": vault_name,
        "label": label or "",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "vars": data,
    }
    snap_dir = _snapshot_dir(
        vault_dir or Path.home() / ".env_vault", vault_name
    )
    (snap_dir / f"{snapshot_id}.json").write_text(json.dumps(meta, indent=2))
    return snapshot_id


def list_snapshots(
    vault_name: str, *, vault_dir: Optional[Path] = None
) -> List[Dict]:
    """Return snapshot metadata dicts sorted oldest-first."""
    snap_dir = _snapshot_dir(
        vault_dir or Path.home() / ".env_vault", vault_name
    )
    results = []
    for f in sorted(snap_dir.glob("*.json")):
        meta = json.loads(f.read_text())
        results.append({k: v for k, v in meta.items() if k != "vars"})
    return results


def restore_snapshot(
    vault_name: str,
    snapshot_id: str,
    password: str,
    *,
    vault_dir: Optional[Path] = None,
) -> int:
    """Overwrite the vault with the contents of *snapshot_id*.

    Returns the number of variables restored.
    """
    snap_dir = _snapshot_dir(
        vault_dir or Path.home() / ".env_vault", vault_name
    )
    snap_file = snap_dir / f"{snapshot_id}.json"
    if not snap_file.exists():
        raise SnapshotError(f"Snapshot '{snapshot_id}' not found for vault '{vault_name}'.")

    meta = json.loads(snap_file.read_text())
    save_vault(vault_name, password, meta["vars"], vault_dir=vault_dir)
    return len(meta["vars"])
