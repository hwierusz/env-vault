"""Main CLI entry point for env-vault."""

import click
from env_vault.storage import load_vault, save_vault, vault_exists, list_vaults
from env_vault.crypto import encrypt, decrypt
from env_vault.cli_export import export_cmd, import_cmd
from env_vault.cli_copy import copy_cmd
from env_vault.cli_merge import merge_cmd
from env_vault.cli_tags import tag_cmd
from env_vault.cli_snapshot import snapshot_cmd
from env_vault.cli_ttl import ttl_cmd
from env_vault.cli_history import history_cmd
from env_vault.cli_template import template_cmd
from env_vault.cli_lock import lock_cmd
from env_vault.cli_backup import backup_cmd
from env_vault.cli_profile import profile_cmd
from env_vault.cli_remind import remind_cmd
from env_vault.cli_alias import alias_cmd
from env_vault.cli_pin import pin_cmd
from env_vault.cli_webhook import webhook_cmd
from env_vault.cli_namespace import namespace_cmd


@click.group()
def cli():
    """env-vault: encrypted environment variable manager."""


@cli.command()
@click.argument("vault")
@click.password_option(prompt="Vault password")
def init(vault, password):
    """Initialise a new vault."""
    if vault_exists(vault):
        click.echo(f"Vault '{vault}' already exists.", err=True)
        raise SystemExit(1)
    save_vault(vault, password, {})
    click.echo(f"Vault '{vault}' created.")


@cli.command(name="set")
@click.argument("vault")
@click.argument("key")
@click.argument("value")
@click.password_option(prompt="Vault password")
def set(vault, key, value, password):
    """Set a variable in a vault."""
    if not vault_exists(vault):
        click.echo(f"Vault '{vault}' does not exist.", err=True)
        raise SystemExit(1)
    data = load_vault(vault, password)
    data[key] = value
    save_vault(vault, password, data)
    click.echo(f"Set '{key}' in vault '{vault}'.")


@cli.command(name="get")
@click.argument("vault")
@click.argument("key")
@click.password_option(prompt="Vault password")
def get(vault, key, password):
    """Get a variable from a vault."""
    if not vault_exists(vault):
        click.echo(f"Vault '{vault}' does not exist.", err=True)
        raise SystemExit(1)
    data = load_vault(vault, password)
    if key not in data:
        click.echo(f"Key '{key}' not found.", err=True)
        raise SystemExit(1)
    click.echo(data[key])


@cli.command(name="list")
@click.argument("vault")
@click.password_option(prompt="Vault password")
def list_vars(vault, password):
    """List all variables in a vault."""
    if not vault_exists(vault):
        click.echo(f"Vault '{vault}' does not exist.", err=True)
        raise SystemExit(1)
    data = load_vault(vault, password)
    for key, value in sorted(data.items()):
        if not key.startswith("__"):
            click.echo(f"{key}={value}")


@cli.command(name="delete")
@click.argument("vault")
@click.argument("key")
@click.password_option(prompt="Vault password")
def delete(vault, key, password):
    """Delete a variable from a vault."""
    if not vault_exists(vault):
        click.echo(f"Vault '{vault}' does not exist.", err=True)
        raise SystemExit(1)
    data = load_vault(vault, password)
    if key not in data:
        click.echo(f"Key '{key}' not found.", err=True)
        raise SystemExit(1)
    del data[key]
    save_vault(vault, password, data)
    click.echo(f"Deleted '{key}' from vault '{vault}'.")


# Register sub-command groups
cli.add_command(export_cmd)
cli.add_command(import_cmd)
cli.add_command(copy_cmd)
cli.add_command(merge_cmd)
cli.add_command(tag_cmd)
cli.add_command(snapshot_cmd)
cli.add_command(ttl_cmd)
cli.add_command(history_cmd)
cli.add_command(template_cmd)
cli.add_command(lock_cmd)
cli.add_command(backup_cmd)
cli.add_command(profile_cmd)
cli.add_command(remind_cmd)
cli.add_command(alias_cmd)
cli.add_command(pin_cmd)
cli.add_command(webhook_cmd)
cli.add_command(namespace_cmd)
