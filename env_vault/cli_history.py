"""CLI commands for variable change history."""

import click

from env_vault.history import HistoryError, clear_history, read_history
from env_vault.storage import DEFAULT_VAULT_DIR


@click.group("history")
def history_cmd():
    """View and manage variable change history."""


@history_cmd.command("show")
@click.argument("vault_name")
@click.option("--key", default=None, help="Filter history to a specific key.")
@click.option("--limit", default=20, show_default=True, help="Maximum entries to show.")
@click.option(
    "--vault-dir",
    default=DEFAULT_VAULT_DIR,
    envvar="ENV_VAULT_DIR",
    show_default=True,
)
def history_show(vault_name: str, key, limit: int, vault_dir: str):
    """Show recent change history for VAULT_NAME."""
    try:
        entries = read_history(vault_name, vault_dir, key=key, limit=limit)
    except HistoryError as exc:
        raise click.ClickException(str(exc))

    if not entries:
        click.echo("No history found.")
        return

    for entry in entries:
        ts = entry.get("timestamp", "?")
        action = entry.get("action", "?")
        k = entry.get("key", "?")
        parts = [f"[{ts}] {action.upper():6s} {k}"]
        if "old_value" in entry:
            parts.append(f"  old={entry['old_value']!r}")
        if "new_value" in entry:
            parts.append(f"  new={entry['new_value']!r}")
        click.echo("".join(parts))


@history_cmd.command("clear")
@click.argument("vault_name")
@click.option(
    "--vault-dir",
    default=DEFAULT_VAULT_DIR,
    envvar="ENV_VAULT_DIR",
    show_default=True,
)
@click.confirmation_option(prompt="Clear all history for this vault?")
def history_clear(vault_name: str, vault_dir: str):
    """Delete all history records for VAULT_NAME."""
    try:
        removed = clear_history(vault_name, vault_dir)
    except HistoryError as exc:
        raise click.ClickException(str(exc))
    click.echo(f"Cleared {removed} history record(s) for '{vault_name}'.")
