"""CLI commands for lineage tracking."""
import json
import click

from env_vault.lineage import (
    LineageError,
    record_lineage,
    get_lineage,
    list_lineage,
    remove_lineage,
)
from env_vault.storage import load_vault, save_vault, vault_exists


def _load(name: str) -> dict:
    return load_vault(name)


def _save(name: str, data: dict) -> None:
    save_vault(name, data)


@click.group("lineage")
def lineage_cmd():
    """Track the origin and derivation of vault keys."""


@lineage_cmd.command("record")
@click.argument("vault")
@click.argument("key")
@click.option("--source", required=True, help="Origin label or vault name.")
@click.option("--derived-from", default=None, help="Parent key this was derived from.")
@click.option("--note", default=None, help="Optional free-text note.")
def lineage_record(vault, key, source, derived_from, note):
    """Record lineage metadata for KEY in VAULT."""
    if not vault_exists(vault):
        click.echo(f"Error: vault '{vault}' does not exist.", err=True)
        raise SystemExit(1)
    try:
        entry = record_lineage(
            vault, key, source,
            derived_from=derived_from, note=note,
            load=_load, save=_save,
        )
        click.echo(f"Recorded lineage for '{entry.key}' (source: {entry.source}).")
    except LineageError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@lineage_cmd.command("show")
@click.argument("vault")
@click.argument("key")
@click.option("--json", "as_json", is_flag=True)
def lineage_show(vault, key, as_json):
    """Show lineage for KEY in VAULT."""
    if not vault_exists(vault):
        click.echo(f"Error: vault '{vault}' does not exist.", err=True)
        raise SystemExit(1)
    entry = get_lineage(vault, key, load=_load)
    if entry is None:
        click.echo(f"No lineage recorded for '{key}'.")
        return
    if as_json:
        click.echo(json.dumps(entry.to_dict(), indent=2))
    else:
        click.echo(f"key:          {entry.key}")
        click.echo(f"source:       {entry.source}")
        click.echo(f"derived_from: {entry.derived_from or '-'}")
        click.echo(f"note:         {entry.note or '-'}")


@lineage_cmd.command("list")
@click.argument("vault")
@click.option("--json", "as_json", is_flag=True)
def lineage_list(vault, as_json):
    """List all lineage entries for VAULT."""
    if not vault_exists(vault):
        click.echo(f"Error: vault '{vault}' does not exist.", err=True)
        raise SystemExit(1)
    entries = list_lineage(vault, load=_load)
    if as_json:
        click.echo(json.dumps([e.to_dict() for e in entries], indent=2))
    else:
        if not entries:
            click.echo("No lineage entries recorded.")
        for e in entries:
            derived = f" <- {e.derived_from}" if e.derived_from else ""
            click.echo(f"  {e.key}: {e.source}{derived}")


@lineage_cmd.command("remove")
@click.argument("vault")
@click.argument("key")
def lineage_remove(vault, key):
    """Remove lineage metadata for KEY in VAULT."""
    if not vault_exists(vault):
        click.echo(f"Error: vault '{vault}' does not exist.", err=True)
        raise SystemExit(1)
    removed = remove_lineage(vault, key, load=_load, save=_save)
    if removed:
        click.echo(f"Lineage for '{key}' removed.")
    else:
        click.echo(f"No lineage entry found for '{key}'.")
