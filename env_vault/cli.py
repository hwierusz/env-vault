"""Main CLI entry point for env-vault."""

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


@click.group()
def cli() -> None:
    """env-vault: encrypted environment variable manager."""


@cli.command()
@click.argument("vault_name")
@click.password_option(prompt="Master password")
def init(vault_name: str, password: str) -> None:
    """Initialise a new vault called VAULT_NAME."""
    if vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' already exists.", err=True)
        raise SystemExit(1)
    save_vault(vault_name, password, {})
    click.echo(f"Vault '{vault_name}' created.")


@cli.command(name="set")
@click.argument("vault_name")
@click.argument("key")
@click.argument("value")
@click.password_option(prompt="Master password")
def set(vault_name: str, key: str, value: str, password: str) -> None:
    """Set KEY=VALUE in VAULT_NAME."""
    if not vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' does not exist.", err=True)
        raise SystemExit(1)
    from env_vault.lock import assert_unlocked, LockError
    try:
        assert_unlocked(vault_name)
    except LockError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    data = load_vault(vault_name, password)
    data[key] = value
    save_vault(vault_name, password, data)
    click.echo(f"Set {key} in '{vault_name}'.")


@cli.command(name="get")
@click.argument("vault_name")
@click.argument("key")
@click.password_option(prompt="Master password")
def get(vault_name: str, key: str, password: str) -> None:
    """Get the value of KEY from VAULT_NAME."""
    if not vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' does not exist.", err=True)
        raise SystemExit(1)
    data = load_vault(vault_name, password)
    if key not in data:
        click.echo(f"Error: key '{key}' not found.", err=True)
        raise SystemExit(1)
    click.echo(data[key])


@cli.command(name="list")
@click.argument("vault_name")
@click.password_option(prompt="Master password")
def list_vars(vault_name: str, password: str) -> None:
    """List all keys stored in VAULT_NAME."""
    if not vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' does not exist.", err=True)
        raise SystemExit(1)
    data = load_vault(vault_name, password)
    if not data:
        click.echo("(empty vault)")
    else:
        for k in sorted(data):
            click.echo(k)


@cli.command(name="delete")
@click.argument("vault_name")
@click.argument("key")
@click.password_option(prompt="Master password")
def delete(vault_name: str, key: str, password: str) -> None:
    """Delete KEY from VAULT_NAME."""
    if not vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' does not exist.", err=True)
        raise SystemExit(1)
    from env_vault.lock import assert_unlocked, LockError
    try:
        assert_unlocked(vault_name)
    except LockError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    data = load_vault(vault_name, password)
    if key not in data:
        click.echo(f"Error: key '{key}' not found.", err=True)
        raise SystemExit(1)
    del data[key]
    save_vault(vault_name, password, data)
    click.echo(f"Deleted {key} from '{vault_name}'.")


cli.add_command(export_cmd, "export")
cli.add_command(import_cmd, "import")
cli.add_command(copy_cmd, "copy")
cli.add_command(merge_cmd, "merge")
cli.add_command(tag_cmd, "tag")
cli.add_command(snapshot_cmd, "snapshot")
cli.add_command(ttl_cmd, "ttl")
cli.add_command(history_cmd, "history")
cli.add_command(template_cmd, "template")
cli.add_command(lock_cmd, "lock")
