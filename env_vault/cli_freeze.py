"""CLI commands for vault freeze/unfreeze."""

import click

from env_vault.freeze import FreezeError, freeze_vault, get_freeze_reason, is_frozen, unfreeze_vault


@click.group("freeze")
def freeze_cmd():
    """Freeze or unfreeze a vault to prevent modifications."""


@freeze_cmd.command("on")
@click.argument("vault")
@click.option("--reason", "-r", default="", help="Optional reason for freezing.")
def freeze_on(vault: str, reason: str):
    """Freeze VAULT, blocking all write operations."""
    try:
        freeze_vault(vault, reason=reason)
        msg = f"Vault '{vault}' is now frozen."
        if reason:
            msg += f" Reason: {reason}"
        click.echo(msg)
    except FreezeError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@freeze_cmd.command("off")
@click.argument("vault")
def freeze_off(vault: str):
    """Unfreeze VAULT, allowing write operations again."""
    try:
        unfreeze_vault(vault)
        click.echo(f"Vault '{vault}' has been unfrozen.")
    except FreezeError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@freeze_cmd.command("status")
@click.argument("vault")
def freeze_status(vault: str):
    """Show the freeze status of VAULT."""
    frozen = is_frozen(vault)
    state = "frozen" if frozen else "unfrozen"
    click.echo(f"Vault '{vault}' is {state}.")
    if frozen:
        reason = get_freeze_reason(vault)
        if reason:
            click.echo(f"Reason: {reason}")
