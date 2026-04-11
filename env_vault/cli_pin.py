"""CLI commands for PIN-based key protection."""

from __future__ import annotations

import click

from env_vault.pin import PinError, list_pinned_keys, remove_pin, set_pin, verify_pin
from env_vault.storage import load_vault, save_vault, vault_exists


@click.group("pin")
def pin_cmd() -> None:
    """Manage PIN protection for individual vault keys."""


@pin_cmd.command("set")
@click.argument("vault")
@click.argument("key")
@click.password_option("--pin", prompt="Enter PIN", confirmation_prompt=True, help="Numeric PIN (min 4 digits).")
def pin_set(vault: str, key: str, pin: str) -> None:
    """Attach a PIN to KEY in VAULT."""
    if not vault_exists(vault):
        raise click.ClickException(f"Vault '{vault}' does not exist.")
    try:
        set_pin(vault, key, pin, load_vault, save_vault)
        click.echo(f"PIN set for '{key}' in vault '{vault}'.")
    except PinError as exc:
        raise click.ClickException(str(exc)) from exc


@pin_cmd.command("remove")
@click.argument("vault")
@click.argument("key")
def pin_remove(vault: str, key: str) -> None:
    """Remove the PIN from KEY in VAULT."""
    if not vault_exists(vault):
        raise click.ClickException(f"Vault '{vault}' does not exist.")
    try:
        remove_pin(vault, key, load_vault, save_vault)
        click.echo(f"PIN removed from '{key}' in vault '{vault}'.")
    except PinError as exc:
        raise click.ClickException(str(exc)) from exc


@pin_cmd.command("verify")
@click.argument("vault")
@click.argument("key")
@click.option("--pin", prompt="Enter PIN", hide_input=True, help="PIN to verify.")
def pin_verify(vault: str, key: str, pin: str) -> None:
    """Check whether PIN is correct for KEY in VAULT."""
    if not vault_exists(vault):
        raise click.ClickException(f"Vault '{vault}' does not exist.")
    if verify_pin(vault, key, pin, load_vault):
        click.echo("PIN accepted.")
    else:
        raise click.ClickException("Incorrect PIN.")


@pin_cmd.command("list")
@click.argument("vault")
def pin_list(vault: str) -> None:
    """List all PIN-protected keys in VAULT."""
    if not vault_exists(vault):
        raise click.ClickException(f"Vault '{vault}' does not exist.")
    keys = list_pinned_keys(vault, load_vault)
    if keys:
        for k in keys:
            click.echo(k)
    else:
        click.echo("No PIN-protected keys.")
