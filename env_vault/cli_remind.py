"""CLI commands for TTL reminders."""

import click

from env_vault.remind import RemindError, check_reminders
from env_vault.storage import load_vault, vault_exists


@click.group("remind")
def remind_cmd():
    """Check which variables are near or past their TTL expiry."""


@remind_cmd.command("check")
@click.argument("vault_name")
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    help="Vault password.",
)
@click.option(
    "--threshold",
    default=86400,
    show_default=True,
    help="Warn when TTL is below this many seconds.",
)
def remind_check(vault_name: str, password: str, threshold: int):
    """List variables expiring within THRESHOLD seconds."""
    if not vault_exists(vault_name):
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")

    try:
        data = load_vault(vault_name, password)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    try:
        entries = check_reminders(vault_name, data, threshold_seconds=threshold)
    except RemindError as exc:
        raise click.ClickException(str(exc)) from exc

    if not entries:
        click.echo("No variables expiring within the threshold.")
        return

    for entry in entries:
        if entry.expired:
            status = click.style("EXPIRED", fg="red", bold=True)
        else:
            hours = int(entry.seconds_remaining // 3600)
            minutes = int((entry.seconds_remaining % 3600) // 60)
            status = click.style(f"{hours}h {minutes}m remaining", fg="yellow")
        click.echo(f"  {entry.key}: {status}")
