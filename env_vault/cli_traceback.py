"""CLI commands for vault variable traceback."""
import json
import click
from env_vault.traceback import record_trace, read_traces, clear_traces, TracebackError
from env_vault.storage import vault_exists


@click.group("traceback")
def traceback_cmd():
    """Record and inspect variable origin traces."""


@traceback_cmd.command("record")
@click.argument("vault")
@click.argument("key")
@click.argument("value")
@click.option("--source", required=True, help="Origin source label")
@click.option("--note", default=None, help="Optional note")
@click.option("--vault-dir", default=".vaults", show_default=True)
def trace_record(vault, key, value, source, note, vault_dir):
    """Record a trace entry for KEY in VAULT."""
    if not vault_exists(vault_dir, vault):
        click.echo(f"Error: vault '{vault}' not found.", err=True)
        raise SystemExit(1)
    try:
        entry = record_trace(vault_dir, vault, key, value, source, note)
        click.echo(f"Recorded trace for '{entry.key}' from '{entry.source}'.")
    except TracebackError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@traceback_cmd.command("show")
@click.argument("vault")
@click.option("--key", default=None, help="Filter by key")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
@click.option("--vault-dir", default=".vaults", show_default=True)
def trace_show(vault, key, fmt, vault_dir):
    """Show trace entries for VAULT."""
    if not vault_exists(vault_dir, vault):
        click.echo(f"Error: vault '{vault}' not found.", err=True)
        raise SystemExit(1)
    entries = read_traces(vault_dir, vault, key=key)
    if not entries:
        click.echo("No trace entries found.")
        return
    if fmt == "json":
        click.echo(json.dumps([e.to_dict() for e in entries], indent=2))
    else:
        for e in entries:
            note_str = f" ({e.note})" if e.note else ""
            click.echo(f"[{e.timestamp}] {e.key} <- {e.source}{note_str}")


@traceback_cmd.command("clear")
@click.argument("vault")
@click.option("--vault-dir", default=".vaults", show_default=True)
def trace_clear(vault, vault_dir):
    """Clear all trace entries for VAULT."""
    if not vault_exists(vault_dir, vault):
        click.echo(f"Error: vault '{vault}' not found.", err=True)
        raise SystemExit(1)
    count = clear_traces(vault_dir, vault)
    click.echo(f"Cleared {count} trace entries.")
