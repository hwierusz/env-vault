"""Main CLI entry-point for env-vault."""

from __future__ import annotations

import click

from env_vault.storage import (
    save_vault,
    load_vault,
    vault_exists,
    list_vaults,
    _vault_path,
)
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
from env_vault.cli_access import access_cmd
from env_vault.cli_quota import quota_cmd
from env_vault.cli_watch import watch_cmd
from env_vault.cli_compress import compress_cmd
from env_vault.cli_cascade import cascade_cmd
from env_vault.cli_rollback import rollback_cmd


@click.group()
def cli() -> None:
    """env-vault: encrypted environment variable manager."""


@cli.command()
@click.argument("vault_name")
@click.option("--vault-dir", default=".", show_default=True)
def init(vault_name: str, vault_dir: str) -> None:
    """Initialise a new vault."""
    if vault_exists(vault_name, vault_dir=vault_dir):
        raise click.ClickException(f"Vault '{vault_name}' already exists.")
    save_vault(vault_name, {}, vault_dir=vault_dir)
    click.echo(f"Vault '{vault_name}' created.")


@cli.command(name="set")
@click.argument("vault_name")
@click.argument("key")
@click.argument("value")
@click.option("--vault-dir", default=".", show_default=True)
def set(vault_name: str, key: str, value: str, vault_dir: str) -> None:  # noqa: A001
    """Set a variable in the vault."""
    if not vault_exists(vault_name, vault_dir=vault_dir):
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")
    data = load_vault(vault_name, vault_dir=vault_dir)
    data[key] = value
    save_vault(vault_name, data, vault_dir=vault_dir)
    click.echo(f"{key} set.")


@cli.command(name="get")
@click.argument("vault_name")
@click.argument("key")
@click.option("--vault-dir", default=".", show_default=True)
def get(vault_name: str, key: str, vault_dir: str) -> None:  # noqa: A001
    """Get a variable from the vault."""
    if not vault_exists(vault_name, vault_dir=vault_dir):
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")
    data = load_vault(vault_name, vault_dir=vault_dir)
    if key not in data:
        raise click.ClickException(f"Key '{key}' not found.")
    click.echo(data[key])


@cli.command(name="list")
@click.argument("vault_name")
@click.option("--vault-dir", default=".", show_default=True)
def list_vars(vault_name: str, vault_dir: str) -> None:
    """List all variables in the vault."""
    if not vault_exists(vault_name, vault_dir=vault_dir):
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")
    data = load_vault(vault_name, vault_dir=vault_dir)
    if not data:
        click.echo("(empty)")
        return
    for k, v in sorted(data.items()):
        click.echo(f"{k}={v}")


@cli.command(name="delete")
@click.argument("vault_name")
@click.argument("key")
@click.option("--vault-dir", default=".", show_default=True)
def delete(vault_name: str, key: str, vault_dir: str) -> None:
    """Delete a variable from the vault."""
    if not vault_exists(vault_name, vault_dir=vault_dir):
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")
    data = load_vault(vault_name, vault_dir=vault_dir)
    if key not in data:
        raise click.ClickException(f"Key '{key}' not found.")
    del data[key]
    save_vault(vault_name, data, vault_dir=vault_dir)
    click.echo(f"{key} deleted.")


for _cmd in [
    export_cmd, import_cmd, copy_cmd, merge_cmd, tag_cmd, snapshot_cmd,
    ttl_cmd, history_cmd, template_cmd, lock_cmd, backup_cmd, profile_cmd,
    remind_cmd, alias_cmd, pin_cmd, webhook_cmd, namespace_cmd, access_cmd,
    quota_cmd, watch_cmd, compress_cmd, cascade_cmd, rollback_cmd,
]:
    cli.add_command(_cmd)
