"""CLI commands for provenance tracking."""
import json

import click

from env_vault.provenance import ProvenanceError, record_provenance, read_provenance, clear_provenance
from env_vault.storage import vault_exists


@click.group("provenance")
def provenance_cmd():
    """Track and query variable provenance."""


def _require_vault(vault_name: str) -> None:
    if not vault_exists(vault_name):
        raise click.ClickException(f"Vault '{vault_name}' not found.")


@provenance_cmd.command("record")
@click.argument("vault_name")
@click.argument("key")
@click.option("--source", required=True, help="Origin of the variable (e.g. CI, manual, script).")
@click.option("--author", required=True, help="Who introduced this variable.")
@click.option("--note", default="", help="Optional free-text note.")
def provenance_record(vault_name, key, source, author, note):
    """Record provenance for KEY in VAULT_NAME."""
    _require_vault(vault_name)
    try:
        entry = record_provenance(vault_name, key, source, author, note)
    except ProvenanceError as exc:
        raise click.ClickException(str(exc))
    click.echo(f"Recorded provenance for '{entry.key}' (source={entry.source}, author={entry.author}).")


@provenance_cmd.command("show")
@click.argument("vault_name")
@click.option("--key", default=None, help="Filter by variable key.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def provenance_show(vault_name, key, fmt):
    """Show provenance records for VAULT_NAME."""
    _require_vault(vault_name)
    entries = read_provenance(vault_name, key=key)
    if not entries:
        click.echo("No provenance records found.")
        return
    if fmt == "json":
        click.echo(json.dumps([e.to_dict() for e in entries], indent=2))
    else:
        for e in entries:
            ts = f"{e.timestamp:.0f}"
            note_part = f"  # {e.note}" if e.note else ""
            click.echo(f"{e.key}  source={e.source}  author={e.author}  ts={ts}{note_part}")


@provenance_cmd.command("clear")
@click.argument("vault_name")
@click.confirmation_option(prompt="Delete all provenance records?")
def provenance_clear(vault_name):
    """Clear all provenance records for VAULT_NAME."""
    _require_vault(vault_name)
    clear_provenance(vault_name)
    click.echo(f"Provenance records for '{vault_name}' cleared.")
