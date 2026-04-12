"""CLI commands for group management."""

from __future__ import annotations

import click

from env_vault.group import (
    GroupError,
    add_to_group,
    delete_group,
    get_group_members,
    get_vars_for_group,
    list_groups,
    remove_from_group,
)
from env_vault.storage import load_vault, save_vault, vault_exists


@click.group("group")
def group_cmd():
    """Manage variable groups."""


@group_cmd.command("add")
@click.argument("vault_name")
@click.argument("group")
@click.argument("key")
@click.password_option(prompt="Vault password")
def group_add(vault_name: str, group: str, key: str, password: str):
    """Add KEY to GROUP in VAULT_NAME."""
    if not vault_exists(vault_name):
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")
    try:
        data = load_vault(vault_name, password)
        add_to_group(data, group, key)
        save_vault(vault_name, password, data)
        click.echo(f"Added '{key}' to group '{group}'.")
    except GroupError as exc:
        raise click.ClickException(str(exc))


@group_cmd.command("remove")
@click.argument("vault_name")
@click.argument("group")
@click.argument("key")
@click.password_option(prompt="Vault password")
def group_remove(vault_name: str, group: str, key: str, password: str):
    """Remove KEY from GROUP in VAULT_NAME."""
    if not vault_exists(vault_name):
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")
    try:
        data = load_vault(vault_name, password)
        remove_from_group(data, group, key)
        save_vault(vault_name, password, data)
        click.echo(f"Removed '{key}' from group '{group}'.")
    except GroupError as exc:
        raise click.ClickException(str(exc))


@group_cmd.command("list")
@click.argument("vault_name")
@click.password_option(prompt="Vault password")
def group_list(vault_name: str, password: str):
    """List all groups in VAULT_NAME."""
    if not vault_exists(vault_name):
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")
    data = load_vault(vault_name, password)
    groups = list_groups(data)
    if not groups:
        click.echo("No groups defined.")
    else:
        for g in groups:
            click.echo(g)


@group_cmd.command("show")
@click.argument("vault_name")
@click.argument("group")
@click.password_option(prompt="Vault password")
def group_show(vault_name: str, group: str, password: str):
    """Show members and values for GROUP in VAULT_NAME."""
    if not vault_exists(vault_name):
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")
    try:
        data = load_vault(vault_name, password)
        members = get_vars_for_group(data, group)
        if not members:
            click.echo(f"Group '{group}' is empty.")
        else:
            for k, v in sorted(members.items()):
                click.echo(f"{k}={v}")
    except GroupError as exc:
        raise click.ClickException(str(exc))


@group_cmd.command("delete")
@click.argument("vault_name")
@click.argument("group")
@click.password_option(prompt="Vault password")
def group_delete(vault_name: str, group: str, password: str):
    """Delete GROUP from VAULT_NAME."""
    if not vault_exists(vault_name):
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")
    try:
        data = load_vault(vault_name, password)
        delete_group(data, group)
        save_vault(vault_name, password, data)
        click.echo(f"Group '{group}' deleted.")
    except GroupError as exc:
        raise click.ClickException(str(exc))
