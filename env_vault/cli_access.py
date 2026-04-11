"""CLI commands for vault access control."""
from __future__ import annotations

import click

from env_vault.access import AccessError, check_access, grant_access, list_access, revoke_access
from env_vault.storage import load_vault, save_vault


@click.group("access")
def access_cmd():
    """Manage access control for a vault."""


@access_cmd.command("grant")
@click.argument("vault_name")
@click.argument("username")
@click.option("-p", "--permission", "permissions", multiple=True,
              default=("read",), show_default=True,
              help="Permission to grant (read/write/admin). Repeatable.")
def access_grant(vault_name: str, username: str, permissions):
    """Grant permissions to USERNAME in VAULT_NAME."""
    try:
        grant_access(vault_name, username, list(permissions), load_vault, save_vault)
        click.echo(f"Granted {list(permissions)} to '{username}' in vault '{vault_name}'.")
    except AccessError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@access_cmd.command("revoke")
@click.argument("vault_name")
@click.argument("username")
@click.option("-p", "--permission", "permissions", multiple=True, default=None,
              help="Permission to revoke. Omit to revoke all.")
def access_revoke(vault_name: str, username: str, permissions):
    """Revoke permissions from USERNAME in VAULT_NAME."""
    perms = list(permissions) if permissions else None
    try:
        revoke_access(vault_name, username, perms, load_vault, save_vault)
        label = str(perms) if perms else "all permissions"
        click.echo(f"Revoked {label} from '{username}' in vault '{vault_name}'.")
    except AccessError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@access_cmd.command("list")
@click.argument("vault_name")
def access_list(vault_name: str):
    """List all access entries for VAULT_NAME."""
    acl = list_access(vault_name, load_vault)
    if not acl:
        click.echo("No access control entries (vault is open).")
        return
    for user, perms in sorted(acl.items()):
        click.echo(f"  {user}: {', '.join(perms)}")


@access_cmd.command("check")
@click.argument("vault_name")
@click.argument("permission")
def access_check(vault_name: str, permission: str):
    """Check if the current user holds PERMISSION in VAULT_NAME."""
    allowed = check_access(vault_name, permission, load_vault)
    if allowed:
        click.echo("Access granted.")
    else:
        click.echo("Access denied.", err=True)
        raise SystemExit(1)
