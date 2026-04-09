"""CLI commands for vault snapshots."""

import click
from pathlib import Path

from env_vault.snapshot import SnapshotError, create_snapshot, list_snapshots, restore_snapshot


@click.group("snapshot")
def snapshot_cmd():
    """Manage point-in-time snapshots of a vault."""


@snapshot_cmd.command("create")
@click.argument("vault_name")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.option("--label", default="", help="Optional human-readable label.")
def snapshot_create(vault_name: str, password: str, label: str):
    """Create a snapshot of VAULT_NAME."""
    try:
        sid = create_snapshot(vault_name, password, label or None)
        click.echo(f"Snapshot created: {sid}")
    except SnapshotError as exc:
        raise click.ClickException(str(exc))


@snapshot_cmd.command("list")
@click.argument("vault_name")
def snapshot_list(vault_name: str):
    """List all snapshots for VAULT_NAME."""
    snaps = list_snapshots(vault_name)
    if not snaps:
        click.echo("No snapshots found.")
        return
    for s in snaps:
        label = f"  [{s['label']}]" if s.get("label") else ""
        click.echo(f"{s['id']}  {s['created_at']}{label}")


@snapshot_cmd.command("restore")
@click.argument("vault_name")
@click.argument("snapshot_id")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.confirmation_option(prompt="This will overwrite the current vault. Continue?")
def snapshot_restore(vault_name: str, snapshot_id: str, password: str):
    """Restore VAULT_NAME from SNAPSHOT_ID."""
    try:
        count = restore_snapshot(vault_name, snapshot_id, password)
        click.echo(f"Restored {count} variable(s) from snapshot {snapshot_id}.")
    except SnapshotError as exc:
        raise click.ClickException(str(exc))
