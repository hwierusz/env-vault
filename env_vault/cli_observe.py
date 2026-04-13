"""CLI commands for the observe (read-access tracking) feature."""
from __future__ import annotations

import json
from pathlib import Path

import click

from env_vault.observe import ObserveError, clear_observations, read_observations
from env_vault.storage import vault_exists

DEFAULT_VAULT_DIR = Path.home() / ".env_vault"


@click.group("observe")
def observe_cmd() -> None:
    """Track and inspect variable read-access events."""


@observe_cmd.command("log")
@click.argument("vault_name")
@click.option("--key", default=None, help="Filter by variable key.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.option("--vault-dir", default=str(DEFAULT_VAULT_DIR), show_default=True)
def observe_log(
    vault_name: str, key: str | None, as_json: bool, vault_dir: str
) -> None:
    """Show read-access log for VAULT_NAME."""
    vd = Path(vault_dir)
    if not vault_exists(vault_name, vault_dir=vd):
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")
    try:
        events = read_observations(vault_name, vault_dir=vd, key=key)
    except ObserveError as exc:
        raise click.ClickException(str(exc)) from exc

    if not events:
        click.echo("No observations recorded.")
        return

    if as_json:
        click.echo(json.dumps(events, indent=2))
    else:
        for ev in events:
            import datetime
            ts = datetime.datetime.utcfromtimestamp(ev["ts"]).strftime("%Y-%m-%d %H:%M:%S")
            click.echo(f"[{ts}] {ev['actor']} read {ev['key']}")


@observe_cmd.command("clear")
@click.argument("vault_name")
@click.option("--vault-dir", default=str(DEFAULT_VAULT_DIR), show_default=True)
def observe_clear(vault_name: str, vault_dir: str) -> None:
    """Clear all read-access observations for VAULT_NAME."""
    vd = Path(vault_dir)
    if not vault_exists(vault_name, vault_dir=vd):
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")
    removed = clear_observations(vault_name, vault_dir=vd)
    click.echo(f"Cleared {removed} observation(s).")
