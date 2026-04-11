"""CLI commands for alias management."""

import click

from env_vault.alias import AliasError, add_alias, list_aliases, remove_alias, resolve_alias


@click.group("alias")
def alias_cmd():
    """Manage variable aliases."""


@alias_cmd.command("add")
@click.argument("vault")
@click.argument("alias")
@click.argument("target")
@click.password_option(prompt="Vault password")
def alias_add(vault: str, alias: str, target: str, password: str):
    """Add ALIAS as a shorthand for TARGET key in VAULT."""
    try:
        add_alias(vault, password, alias, target)
        click.echo(f"Alias '{alias}' -> '{target}' added.")
    except AliasError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@alias_cmd.command("remove")
@click.argument("vault")
@click.argument("alias")
@click.password_option(prompt="Vault password")
def alias_remove(vault: str, alias: str, password: str):
    """Remove ALIAS from VAULT."""
    try:
        remove_alias(vault, password, alias)
        click.echo(f"Alias '{alias}' removed.")
    except AliasError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@alias_cmd.command("resolve")
@click.argument("vault")
@click.argument("alias")
@click.password_option(prompt="Vault password")
def alias_resolve(vault: str, alias: str, password: str):
    """Show the key that ALIAS points to."""
    try:
        key = resolve_alias(vault, password, alias)
        if key is None:
            click.echo(f"Alias '{alias}' not found.", err=True)
            raise SystemExit(1)
        click.echo(key)
    except AliasError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@alias_cmd.command("list")
@click.argument("vault")
@click.password_option(prompt="Vault password")
def alias_list(vault: str, password: str):
    """List all aliases defined in VAULT."""
    try:
        aliases = list_aliases(vault, password)
        if not aliases:
            click.echo("No aliases defined.")
        else:
            for alias, key in sorted(aliases.items()):
                click.echo(f"{alias} -> {key}")
    except AliasError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
