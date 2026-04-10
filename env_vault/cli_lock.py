"""CLI commands for vault locking/unlocking."""

import click

from env_vault.lock import LockError, get_lock_info, is_locked, lock_vault, unlock_vault


@click.group("lock")
def lock_cmd() -> None:
    """Lock and unlock vaults to prevent accidental modifications."""


@lock_cmd.command("on")
@click.argument("vault_name")
@click.option("--reason", "-r", default="", help="Human-readable reason for locking.")
def lock_on(vault_name: str, reason: str) -> None:
    """Lock VAULT_NAME."""
    try:
        lock_vault(vault_name, reason=reason)
        click.echo(f"Vault '{vault_name}' locked.")
        if reason:
            click.echo(f"Reason: {reason}")
    except LockError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@lock_cmd.command("off")
@click.argument("vault_name")
def lock_off(vault_name: str) -> None:
    """Unlock VAULT_NAME."""
    try:
        unlock_vault(vault_name)
        click.echo(f"Vault '{vault_name}' unlocked.")
    except LockError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@lock_cmd.command("status")
@click.argument("vault_name")
def lock_status(vault_name: str) -> None:
    """Show lock status for VAULT_NAME."""
    info = get_lock_info(vault_name)
    if info is None:
        click.echo(f"Vault '{vault_name}' is unlocked.")
    else:
        import datetime

        ts = datetime.datetime.fromtimestamp(info["locked_at"]).isoformat()
        reason = info.get("reason") or "none"
        click.echo(f"Vault '{vault_name}' is LOCKED.")
        click.echo(f"  Since : {ts}")
        click.echo(f"  Reason: {reason}")
