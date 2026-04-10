"""CLI commands for TTL management."""

import click
from env_vault.storage import load_vault, save_vault, vault_exists
from env_vault.ttl import TTLError, set_ttl, get_ttl, remove_ttl, purge_expired
import time


@click.group(name="ttl")
def ttl_cmd():
    """Manage expiry (TTL) for vault variables."""


@ttl_cmd.command(name="set")
@click.argument("vault_name")
@click.argument("key")
@click.argument("seconds", type=int)
@click.option("--password", prompt=True, hide_input=True)
def ttl_set(vault_name, key, seconds, password):
    """Set a TTL of SECONDS on KEY in VAULT_NAME."""
    if not vault_exists(vault_name):
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")
    try:
        data = load_vault(vault_name, password)
        data = set_ttl(data, key, seconds)
        save_vault(vault_name, data, password)
        click.echo(f"TTL of {seconds}s set for '{key}'.")
    except TTLError as exc:
        raise click.ClickException(str(exc))


@ttl_cmd.command(name="get")
@click.argument("vault_name")
@click.argument("key")
@click.option("--password", prompt=True, hide_input=True)
def ttl_get(vault_name, key, password):
    """Show remaining TTL for KEY in VAULT_NAME."""
    if not vault_exists(vault_name):
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")
    data = load_vault(vault_name, password)
    expiry = get_ttl(data, key)
    if expiry is None:
        click.echo(f"'{key}' has no TTL.")
    else:
        remaining = expiry - time.time()
        if remaining <= 0:
            click.echo(f"'{key}' has expired.")
        else:
            click.echo(f"'{key}' expires in {remaining:.1f}s.")


@ttl_cmd.command(name="remove")
@click.argument("vault_name")
@click.argument("key")
@click.option("--password", prompt=True, hide_input=True)
def ttl_remove(vault_name, key, password):
    """Remove TTL from KEY in VAULT_NAME."""
    if not vault_exists(vault_name):
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")
    data = load_vault(vault_name, password)
    data = remove_ttl(data, key)
    save_vault(vault_name, data, password)
    click.echo(f"TTL removed from '{key}'.")


@ttl_cmd.command(name="purge")
@click.argument("vault_name")
@click.option("--password", prompt=True, hide_input=True)
def ttl_purge(vault_name, password):
    """Delete all expired variables from VAULT_NAME."""
    if not vault_exists(vault_name):
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")
    data = load_vault(vault_name, password)
    removed = purge_expired(data)
    save_vault(vault_name, data, password)
    if removed:
        click.echo(f"Purged {len(removed)} expired key(s): {', '.join(removed)}")
    else:
        click.echo("No expired keys found.")
