import sys
import click
from env_vault.storage import save_vault, load_vault, vault_exists, list_vaults
from env_vault.crypto import encrypt, decrypt


@click.group()
def cli():
    """env-vault: Manage environment variables with encrypted storage."""
    pass


@cli.command()
@click.argument("vault_name")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True, help="Vault password")
def init(vault_name, password):
    """Initialize a new vault."""
    if vault_exists(vault_name):
        click.echo(f"Vault '{vault_name}' already exists.", err=True)
        sys.exit(1)
    save_vault(vault_name, {}, password)
    click.echo(f"Vault '{vault_name}' created.")


@cli.command()
@click.argument("vault_name")
@click.argument("key")
@click.argument("value")
@click.option("--password", prompt=True, hide_input=True, help="Vault password")
def set(vault_name, key, value, password):
    """Set an environment variable in a vault."""
    if not vault_exists(vault_name):
        click.echo(f"Vault '{vault_name}' does not exist.", err=True)
        sys.exit(1)
    try:
        data = load_vault(vault_name, password)
    except Exception:
        click.echo("Failed to unlock vault. Wrong password?", err=True)
        sys.exit(1)
    data[key] = value
    save_vault(vault_name, data, password)
    click.echo(f"Set '{key}' in vault '{vault_name}'.")


@cli.command(name="get")
@click.argument("vault_name")
@click.argument("key")
@click.option("--password", prompt=True, hide_input=True, help="Vault password")
def get(vault_name, key, password):
    """Get an environment variable from a vault."""
    if not vault_exists(vault_name):
        click.echo(f"Vault '{vault_name}' does not exist.", err=True)
        sys.exit(1)
    try:
        data = load_vault(vault_name, password)
    except Exception:
        click.echo("Failed to unlock vault. Wrong password?", err=True)
        sys.exit(1)
    if key not in data:
        click.echo(f"Key '{key}' not found in vault '{vault_name}'.", err=True)
        sys.exit(1)
    click.echo(data[key])


@cli.command(name="list")
@click.argument("vault_name")
@click.option("--password", prompt=True, hide_input=True, help="Vault password")
def list_vars(vault_name, password):
    """List all keys in a vault."""
    if not vault_exists(vault_name):
        click.echo(f"Vault '{vault_name}' does not exist.", err=True)
        sys.exit(1)
    try:
        data = load_vault(vault_name, password)
    except Exception:
        click.echo("Failed to unlock vault. Wrong password?", err=True)
        sys.exit(1)
    if not data:
        click.echo("(empty vault)")
    for k, v in data.items():
        click.echo(f"{k}={v}")


@cli.command()
def vaults():
    """List all available vaults."""
    names = list_vaults()
    if not names:
        click.echo("No vaults found.")
    for name in names:
        click.echo(name)


if __name__ == "__main__":
    cli()
