"""CLI commands for the permission module."""

from __future__ import annotations

import click

from env_vault.permission import (
    PermissionError,
    check_permission,
    grant_permission,
    list_permissions,
    revoke_permission,
)
from env_vault.storage import load_vault, save_vault, vault_exists


@click.group("permission")
def permission_cmd() -> None:
    """Manage user permissions on vaults."""


def _require_vault(vault_name: str) -> None:
    if not vault_exists(vault_name):
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")


@permission_cmd.command("grant")
@click.argument("vault_name")
@click.argument("user")
@click.argument("permission")
def perm_grant(vault_name: str, user: str, permission: str) -> None:
    """Grant PERMISSION to USER on VAULT_NAME."""
    _require_vault(vault_name)
    try:
        grant_permission(vault_name, user, permission, load_vault, save_vault)
        click.echo(f"Granted '{permission}' to '{user}' on vault '{vault_name}'.")
    except PermissionError as exc:
        raise click.ClickException(str(exc)) from exc


@permission_cmd.command("revoke")
@click.argument("vault_name")
@click.argument("user")
@click.argument("permission")
def perm_revoke(vault_name: str, user: str, permission: str) -> None:
    """Revoke PERMISSION from USER on VAULT_NAME."""
    _require_vault(vault_name)
    try:
        revoke_permission(vault_name, user, permission, load_vault, save_vault)
        click.echo(f"Revoked '{permission}' from '{user}' on vault '{vault_name}'.")
    except PermissionError as exc:
        raise click.ClickException(str(exc)) from exc


@permission_cmd.command("list")
@click.argument("vault_name")
@click.option("--user", default=None, help="Filter by user.")
def perm_list(vault_name: str, user: str) -> None:
    """List permissions on VAULT_NAME."""
    _require_vault(vault_name)
    result = list_permissions(vault_name, user, load_vault)
    if not result:
        click.echo("No permissions set.")
        return
    for u, perms in sorted(result.items()):
        click.echo(f"{u}: {', '.join(sorted(perms))}")


@permission_cmd.command("check")
@click.argument("vault_name")
@click.argument("user")
@click.argument("permission")
def perm_check(vault_name: str, user: str, permission: str) -> None:
    """Check whether USER holds PERMISSION on VAULT_NAME."""
    _require_vault(vault_name)
    has_it = check_permission(vault_name, user, permission, load_vault)
    status = "YES" if has_it else "NO"
    click.echo(f"{user} {permission}: {status}")
