"""CLI commands for immutable key management."""

import click
from env_vault.immutable import lock_key, unlock_key, is_locked, list_locked, ImmutableError


@click.group("immutable", help="Lock keys to prevent modification or deletion.")
def immutable_cmd():
    pass


@immutable_cmd.command("lock")
@click.argument("vault")
@click.argument("key")
@click.option("--reason", default="", help="Optional reason for locking.")
def imm_lock(vault: str, key: str, reason: str):
    """Lock KEY in VAULT so it cannot be changed."""
    try:
        lock_key(vault, key, reason=reason)
        click.echo(f"Key '{key}' in vault '{vault}' is now immutable.")
    except ImmutableError as exc:
        raise click.ClickException(str(exc))


@immutable_cmd.command("unlock")
@click.argument("vault")
@click.argument("key")
def imm_unlock(vault: str, key: str):
    """Remove the immutable lock from KEY in VAULT."""
    try:
        unlock_key(vault, key)
        click.echo(f"Key '{key}' in vault '{vault}' is now mutable.")
    except ImmutableError as exc:
        raise click.ClickException(str(exc))


@immutable_cmd.command("status")
@click.argument("vault")
@click.argument("key")
def imm_status(vault: str, key: str):
    """Show whether KEY in VAULT is locked."""
    locked = is_locked(vault, key)
    state = "LOCKED" if locked else "mutable"
    click.echo(f"{key}: {state}")


@immutable_cmd.command("list")
@click.argument("vault")
def imm_list(vault: str):
    """List all locked keys in VAULT."""
    locked = list_locked(vault)
    if not locked:
        click.echo("No locked keys.")
        return
    for key, meta in locked.items():
        reason = meta.get("reason") or ""
        suffix = f"  # {reason}" if reason else ""
        click.echo(f"  {key}{suffix}")
