"""CLI commands for the vault catalog."""
import json
import click

from env_vault.catalog import (
    CatalogError,
    register_vault,
    unregister_vault,
    get_entry,
    list_catalog,
    search_catalog,
)
from env_vault.storage import load_vault, save_vault, vault_exists


@click.group("catalog")
def catalog_cmd():
    """Manage the vault catalog (descriptions, owners, tags)."""


def _require_vault(name: str):
    if not vault_exists(name):
        raise click.ClickException(f"Vault '{name}' does not exist.")


@catalog_cmd.command("register")
@click.argument("vault")
@click.option("--desc", default="", help="Short description.")
@click.option("--owner", default="", help="Owner identifier.")
@click.option("--tag", "tags", multiple=True, help="Tags (repeatable).")
@click.password_option(prompt="Password")
def catalog_register(vault, desc, owner, tags, password):
    """Register or update a vault in the catalog."""
    _require_vault(vault)
    data = load_vault(vault, password)
    entry = register_vault(vault, data, description=desc, owner=owner, tags=list(tags))
    save_vault(vault, password, data)
    click.echo(f"Registered '{vault}' in catalog.")
    if entry.owner:
        click.echo(f"  owner: {entry.owner}")
    if entry.tags:
        click.echo(f"  tags: {', '.join(entry.tags)}")


@catalog_cmd.command("unregister")
@click.argument("vault")
@click.password_option(prompt="Password")
def catalog_unregister(vault, password):
    """Remove a vault from the catalog."""
    _require_vault(vault)
    data = load_vault(vault, password)
    try:
        unregister_vault(vault, data)
    except CatalogError as exc:
        raise click.ClickException(str(exc))
    save_vault(vault, password, data)
    click.echo(f"Unregistered '{vault}' from catalog.")


@catalog_cmd.command("list")
@click.argument("vault")
@click.option("--tag", default=None, help="Filter by tag.")
@click.option("--owner", default=None, help="Filter by owner.")
@click.option("--json", "as_json", is_flag=True)
@click.password_option(prompt="Password")
def catalog_list(vault, tag, owner, as_json, password):
    """List catalog entries."""
    _require_vault(vault)
    data = load_vault(vault, password)
    entries = search_catalog(data, tag=tag, owner=owner)
    if as_json:
        click.echo(json.dumps([e.to_dict() for e in entries], indent=2))
        return
    if not entries:
        click.echo("No catalog entries found.")
        return
    for e in entries:
        click.echo(f"[{e.vault}] owner={e.owner or '-'} tags={','.join(e.tags) or '-'}")
        if e.description:
            click.echo(f"  {e.description}")
