"""CLI commands for lifecycle management."""

import click

from env_vault.lifecycle import LifecycleError, set_lifecycle, get_lifecycle, list_lifecycle, remove_lifecycle
from env_vault.storage import load_vault, save_vault, vault_exists


def _load(name):
    return load_vault(name)


def _save(name, data):
    save_vault(name, data)


@click.group(name="lifecycle")
def lifecycle_cmd():
    """Manage key lifecycle states (active, deprecated, archived)."""


@lifecycle_cmd.command("set")
@click.argument("vault")
@click.argument("key")
@click.argument("state")
@click.option("--note", default=None, help="Optional note about the state change.")
def lifecycle_set(vault, key, state, note):
    """Set lifecycle STATE for KEY in VAULT."""
    if not vault_exists(vault):
        click.echo(f"Error: vault '{vault}' does not exist.", err=True)
        raise SystemExit(1)
    try:
        entry = set_lifecycle(vault, key, state, note, _load, _save)
        click.echo(f"Set '{key}' lifecycle to '{entry.state}'.")
    except LifecycleError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@lifecycle_cmd.command("get")
@click.argument("vault")
@click.argument("key")
def lifecycle_get(vault, key):
    """Get lifecycle state for KEY in VAULT."""
    if not vault_exists(vault):
        click.echo(f"Error: vault '{vault}' does not exist.", err=True)
        raise SystemExit(1)
    entry = get_lifecycle(vault, key, _load)
    if entry is None:
        click.echo(f"No lifecycle record for '{key}'.")
    else:
        click.echo(f"{entry.key}: {entry.state} (updated: {entry.updated_at})")
        if entry.note:
            click.echo(f"  note: {entry.note}")


@lifecycle_cmd.command("list")
@click.argument("vault")
def lifecycle_list(vault):
    """List all lifecycle records in VAULT."""
    if not vault_exists(vault):
        click.echo(f"Error: vault '{vault}' does not exist.", err=True)
        raise SystemExit(1)
    entries = list_lifecycle(vault, _load)
    if not entries:
        click.echo("No lifecycle records found.")
    for e in entries:
        click.echo(f"{e.key}: {e.state}")


@lifecycle_cmd.command("remove")
@click.argument("vault")
@click.argument("key")
def lifecycle_remove(vault, key):
    """Remove lifecycle record for KEY in VAULT."""
    if not vault_exists(vault):
        click.echo(f"Error: vault '{vault}' does not exist.", err=True)
        raise SystemExit(1)
    removed = remove_lifecycle(vault, key, _load, _save)
    if removed:
        click.echo(f"Removed lifecycle record for '{key}'.")
    else:
        click.echo(f"No lifecycle record found for '{key}'.")
