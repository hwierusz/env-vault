"""CLI commands for vault watching."""

from __future__ import annotations

import threading
import click

from env_vault.watch import WatchEvent, WatchError, watch_vault


@click.group(name="watch")
def watch_cmd() -> None:
    """Watch a vault for live changes."""


@watch_cmd.command(name="start")
@click.argument("vault_name")
@click.option("--password", "-p", prompt=True, hide_input=True, help="Vault password.")
@click.option(
    "--interval",
    "-i",
    default=2.0,
    show_default=True,
    type=float,
    help="Poll interval in seconds.",
)
def watch_start(vault_name: str, password: str, interval: float) -> None:
    """Watch VAULT_NAME and print changes as they occur."""
    stop_event = threading.Event()

    def _on_change(event: WatchEvent) -> None:
        if event.added:
            for k, v in event.added.items():
                click.echo(f"[+] {k}={v}")
        if event.removed:
            for k in event.removed:
                click.echo(f"[-] {k}")
        if event.changed:
            for k, v in event.changed.items():
                click.echo(f"[~] {k}={v}")

    click.echo(
        f"Watching '{vault_name}' every {interval}s — press Ctrl+C to stop."
    )
    try:
        watch_vault(
            vault_name,
            password,
            callback=_on_change,
            interval=interval,
            stop_event=stop_event,
        )
    except WatchError as exc:
        raise click.ClickException(str(exc))
    except KeyboardInterrupt:
        stop_event.set()
        click.echo("\nStopped watching.")
