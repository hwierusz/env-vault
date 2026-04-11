"""CLI commands for managing per-vault variable quotas."""

from __future__ import annotations

import click

from env_vault.quota import (
    QuotaError,
    check_quota,
    get_quota,
    remove_quota,
    set_quota,
)
from env_vault.storage import load_vault, save_vault, vault_exists


@click.group("quota")
def quota_cmd() -> None:
    """Manage variable quotas for a vault."""


@quota_cmd.command("set")
@click.argument("vault_name")
@click.argument("limit", type=int)
def quota_set(vault_name: str, limit: int) -> None:
    """Set the variable quota LIMIT for VAULT_NAME."""
    if not vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' does not exist.", err=True)
        raise SystemExit(1)
    try:
        set_quota(vault_name, limit, load_vault, save_vault)
        click.echo(f"Quota for '{vault_name}' set to {limit} variable(s).")
    except QuotaError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@quota_cmd.command("get")
@click.argument("vault_name")
def quota_get(vault_name: str) -> None:
    """Show the current quota limit for VAULT_NAME."""
    if not vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' does not exist.", err=True)
        raise SystemExit(1)
    limit = get_quota(vault_name, load_vault)
    click.echo(f"Quota limit for '{vault_name}': {limit}")


@quota_cmd.command("remove")
@click.argument("vault_name")
def quota_remove(vault_name: str) -> None:
    """Remove the custom quota from VAULT_NAME (resets to default)."""
    if not vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' does not exist.", err=True)
        raise SystemExit(1)
    remove_quota(vault_name, load_vault, save_vault)
    click.echo(f"Custom quota removed from '{vault_name}'.")


@quota_cmd.command("status")
@click.argument("vault_name")
def quota_status(vault_name: str) -> None:
    """Show current usage vs quota for VAULT_NAME."""
    if not vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' does not exist.", err=True)
        raise SystemExit(1)
    current, limit = check_quota(vault_name, load_vault)
    pct = int(current / limit * 100) if limit else 0
    click.echo(f"{vault_name}: {current}/{limit} variables used ({pct}%)")
