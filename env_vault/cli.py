"""Main CLI entry-point for env-vault."""

import click

from env_vault.storage import load_vault, save_vault, vault_exists
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


@click.group()
def cli():
    """env-vault: encrypted environment variable manager."""


@cli.command()
@click.argument("vault_name")
@click.password_option(prompt="New vault password")
def init(vault_name: str, password: str):
    """Initialise a new vault."""
    if vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' already exists.", err=True)
        raise SystemExit(1)
    save_vault(vault_name, password, {})
    click.echo(f"Vault '{vault_name}' created.")


@cli.command(name="set")
@click.argument("vault_name")
@click.argument("key")
@click.argument("value")
@click.password_option(prompt="Vault password")
def set(vault_name: str, key: str, value: str, password: str):  # noqa: A001
    """Set a variable in a vault."""
    if not vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' not found.", err=True)
        raise SystemExit(1)
    data = load_vault(vault_name, password)
    data[key] = value
    save_vault(vault_name, password, data)
    click.echo(f"Set {key} in '{vault_name}'.")


@cli.command(name="get")
@click.argument("vault_name")
@click.argument("key")
@click.password_option(prompt="Vault password")
def get(vault_name: str, key: str, password: str):  # noqa: A001
    """Get a variable from a vault."""
    if not vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' not found.", err=True)
        raise SystemExit(1)
    data = load_vault(vault_name, password)
    if key not in data:
        click.echo(f"Error: key '{key}' not found.", err=True)
        raise SystemExit(1)
    click.echo(data[key])


@cli.command(name="list")
@click.argument("vault_name")
@click.password_option(prompt="Vault password")
def list_vars(vault_name: str, password: str):
    """List all variables in a vault."""
    if not vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' not found.", err=True)
        raise SystemExit(1)
    data = load_vault(vault_name, password)
    for k, v in data.items():
        click.echo(f"{k}={v}")


@cli.command(name="delete")
@click.argument("vault_name")
@click.argument("key")
@click.password_option(prompt="Vault password")
def delete(vault_name: str, key: str, password: str):
    """Delete a variable from a vault."""
    if not vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' not found.", err=True)
        raise SystemExit(1)
    data = load_vault(vault_name, password)
    if key not in data:
        click.echo(f"Error: key '{key}' not found.", err=True)
        raise SystemExit(1)
    del data[key]
    save_vault(vault_name, password, data)
    click.echo(f"Deleted '{key}' from '{vault_name}'.")


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
