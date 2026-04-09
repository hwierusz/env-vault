"""Main CLI entry-point for env-vault."""

import sys
import click

from env_vault.storage import load_vault, save_vault, vault_exists, list_vaults
from env_vault.cli_export import export_cmd, import_cmd


@click.group()
def cli() -> None:
    """env-vault — encrypted environment variable manager."""


@cli.command()
@click.argument("project")
@click.password_option(prompt="New vault password")
def init(project: str, password: str) -> None:
    """Initialise a new vault for PROJECT."""
    if vault_exists(project):
        click.echo(f"Error: vault '{project}' already exists.", err=True)
        sys.exit(1)
    save_vault(project, {}, password)
    click.echo(f"Vault '{project}' created.")


@cli.command(name="set")
@click.argument("project")
@click.argument("key")
@click.argument("value")
@click.password_option("--password", prompt="Vault password", confirmation_prompt=False)
def set(project: str, key: str, value: str, password: str) -> None:
    """Set KEY=VALUE in PROJECT vault."""
    if not vault_exists(project):
        click.echo(f"Error: vault '{project}' does not exist.", err=True)
        sys.exit(1)
    try:
        data = load_vault(project, password)
    except Exception:
        click.echo("Error: failed to decrypt vault. Wrong password?", err=True)
        sys.exit(1)
    data[key] = value
    save_vault(project, data, password)
    click.echo(f"Set '{key}' in vault '{project}'.")


@cli.command(name="get")
@click.argument("project")
@click.argument("key")
@click.password_option("--password", prompt="Vault password", confirmation_prompt=False)
def get(project: str, key: str, password: str) -> None:
    """Get the value of KEY from PROJECT vault."""
    if not vault_exists(project):
        click.echo(f"Error: vault '{project}' does not exist.", err=True)
        sys.exit(1)
    try:
        data = load_vault(project, password)
    except Exception:
        click.echo("Error: failed to decrypt vault. Wrong password?", err=True)
        sys.exit(1)
    if key not in data:
        click.echo(f"Error: key '{key}' not found.", err=True)
        sys.exit(1)
    click.echo(data[key])


@cli.command(name="list")
@click.argument("project")
@click.password_option("--password", prompt="Vault password", confirmation_prompt=False)
def list_vars(project: str, password: str) -> None:
    """List all variable names in PROJECT vault."""
    if not vault_exists(project):
        click.echo(f"Error: vault '{project}' does not exist.", err=True)
        sys.exit(1)
    try:
        data = load_vault(project, password)
    except Exception:
        click.echo("Error: failed to decrypt vault. Wrong password?", err=True)
        sys.exit(1)
    if not data:
        click.echo("(no variables stored)")
    else:
        for k in sorted(data):
            click.echo(k)


@cli.command(name="vaults")
def vaults() -> None:
    """List all available vaults."""
    names = list_vaults()
    if not names:
        click.echo("(no vaults found)")
    else:
        for name in sorted(names):
            click.echo(name)


cli.add_command(export_cmd, name="export")
cli.add_command(import_cmd, name="import")
