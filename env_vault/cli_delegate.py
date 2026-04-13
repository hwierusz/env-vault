"""CLI commands for key delegation."""
import click

from env_vault.delegate import (
    DelegateError,
    add_delegate,
    remove_delegate,
    resolve_delegate,
    list_delegates,
)
from env_vault.storage import load_vault, save_vault, vault_exists


@click.group("delegate")
def delegate_cmd() -> None:
    """Manage key delegations."""


def _load(name: str):
    if not vault_exists(name):
        raise click.ClickException(f"Vault {name!r} does not exist")
    return load_vault(name)


@delegate_cmd.command("add")
@click.argument("vault")
@click.argument("key")
@click.argument("target")
@click.option("--desc", default="", help="Optional description")
def delegate_add(vault: str, key: str, target: str, desc: str) -> None:
    """Delegate KEY to TARGET within VAULT."""
    try:
        add_delegate(
            vault, key, target, description=desc,
            load=_load, save=save_vault,
        )
        click.echo(f"Delegated '{key}' -> '{target}'")
    except DelegateError as exc:
        raise click.ClickException(str(exc)) from exc


@delegate_cmd.command("remove")
@click.argument("vault")
@click.argument("key")
def delegate_remove(vault: str, key: str) -> None:
    """Remove the delegation for KEY in VAULT."""
    try:
        remove_delegate(vault, key, load=_load, save=save_vault)
        click.echo(f"Delegation for '{key}' removed")
    except DelegateError as exc:
        raise click.ClickException(str(exc)) from exc


@delegate_cmd.command("resolve")
@click.argument("vault")
@click.argument("key")
def delegate_resolve(vault: str, key: str) -> None:
    """Resolve KEY following its delegation chain in VAULT."""
    try:
        value = resolve_delegate(vault, key, load=_load)
        if value is None:
            raise click.ClickException(f"Key {key!r} has no value")
        click.echo(value)
    except DelegateError as exc:
        raise click.ClickException(str(exc)) from exc


@delegate_cmd.command("list")
@click.argument("vault")
def delegate_list(vault: str) -> None:
    """List all delegations in VAULT."""
    entries = list_delegates(vault, load=_load)
    if not entries:
        click.echo("No delegations defined")
        return
    for e in entries:
        desc = f"  # {e.description}" if e.description else ""
        click.echo(f"{e.key} -> {e.target}{desc}")
