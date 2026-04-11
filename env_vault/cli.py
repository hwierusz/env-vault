"""Main CLI entry point for env-vault."""

import click

from env_vault.storage import save_vault, load_vault, vault_exists, list_vaults
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


@click.group()
def cli():
    """env-vault: encrypted environment variable manager."""


@cli.command()
@click.argument("vault_name")
@click.password_option(prompt="Set vault password")
def init(vault_name: str, password: str):
    """Initialise a new vault."""
    if vault_exists(vault_name):
        raise click.ClickException(f"Vault '{vault_name}' already exists.")
    save_vault(vault_name, password, {})
    click.echo(f"Vault '{vault_name}' created.")


@cli.command(name="set")
@click.argument("vault_name")
@click.argument("key")
@click.argument("value")
@click.password_option("--password", "-p", prompt="Vault password")
def set(vault_name: str, key: str, value: str, password: str):
    """Set a variable in a vault."""
    if not vault_exists(vault_name):
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")
    data = load_vault(vault_name, password)
    data[key] = value
    save_vault(vault_name, password, data)
    click.echo(f"Set '{key}' in vault '{vault_name}'.")


@cli.command(name="get")
@click.argument("vault_name")
@click.argument("key")
@click.password_option("--password", "-p", prompt="Vault password")
def get(vault_name: str, key: str, password: str):
    """Get a variable from a vault."""
    if not vault_exists(vault_name):
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")
    data = load_vault(vault_name, password)
    if key not in data:
        raise click.ClickException(f"Key '{key}' not found.")
    click.echo(data[key])


@cli.command(name="list")
@click.argument("vault_name")
@click.password_option("--password", "-p", prompt="Vault password")
def list_vars(vault_name: str, password: str):
    """List all variables in a vault."""
    if not vault_exists(vault_name):
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")
    data = load_vault(vault_name, password)
    keys = [k for k in data if not k.startswith("__")]
    if not keys:
        click.echo("No variables set.")
    else:
        for k in keys:
            click.echo(k)


@cli.command(name="delete")
@click.argument("vault_name")
@click.argument("key")
@click.password_option("--password", "-p", prompt="Vault password")
def delete(vault_name: str, key: str, password: str):
    """Delete a variable from a vault."""
    if not vault_exists(vault_name):
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")
    data = load_vault(vault_name, password)
    if key not in data:
        raise click.ClickException(f"Key '{key}' not found.")
    del data[key]
    save_vault(vault_name, password, data)
    click.echo(f"Deleted '{key}' from vault '{vault_name}'.")


cli.add_command(export_cmd, name="export")
cli.add_command(import_cmd, name="import")
cli.add_command(copy_cmd, name="copy")
cli.add_command(merge_cmd, name="merge")
cli.add_command(tag_cmd, name="tag")
cli.add_command(snapshot_cmd, name="snapshot")
cli.add_command(ttl_cmd, name="ttl")
cli.add_command(history_cmd, name="history")
cli.add_command(template_cmd, name="template")
cli.add_command(lock_cmd, name="lock")
cli.add_command(backup_cmd, name="backup")
cli.add_command(profile_cmd, name="profile")
cli.add_command(remind_cmd, name="remind")
cli.add_command(alias_cmd, name="alias")
cli.add_command(pin_cmd, name="pin")
cli.add_command(webhook_cmd, name="webhook")
