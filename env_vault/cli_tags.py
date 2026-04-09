"""CLI commands for tag management."""

import click
from env_vault.tags import add_tag, remove_tag, list_tags, find_by_tag, TagError


@click.group("tag")
def tag_cmd():
    """Manage tags on vault variables."""
    pass


@tag_cmd.command("add")
@click.argument("vault_name")
@click.argument("key")
@click.argument("tag")
@click.password_option(prompt="Vault password", confirmation_prompt=False)
def tag_add(vault_name, key, tag, password):
    """Add TAG to KEY in VAULT_NAME."""
    try:
        add_tag(vault_name, password, key, tag)
        click.echo(f"Tag '{tag}' added to '{key}' in vault '{vault_name}'.")
    except TagError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@tag_cmd.command("remove")
@click.argument("vault_name")
@click.argument("key")
@click.argument("tag")
@click.password_option(prompt="Vault password", confirmation_prompt=False)
def tag_remove(vault_name, key, tag, password):
    """Remove TAG from KEY in VAULT_NAME."""
    try:
        remove_tag(vault_name, password, key, tag)
        click.echo(f"Tag '{tag}' removed from '{key}' in vault '{vault_name}'.")
    except TagError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@tag_cmd.command("list")
@click.argument("vault_name")
@click.option("--key", default=None, help="Show tags for a specific key only.")
@click.password_option(prompt="Vault password", confirmation_prompt=False)
def tag_list(vault_name, key, password):
    """List tags in VAULT_NAME."""
    tags_index = list_tags(vault_name, password, key=key)
    if not tags_index:
        click.echo("No tags found.")
        return
    for k, tags in tags_index.items():
        click.echo(f"{k}: {', '.join(tags)}")


@tag_cmd.command("find")
@click.argument("vault_name")
@click.argument("tag")
@click.password_option(prompt="Vault password", confirmation_prompt=False)
def tag_find(vault_name, tag, password):
    """Find all variables in VAULT_NAME with TAG."""
    keys = find_by_tag(vault_name, password, tag)
    if not keys:
        click.echo(f"No variables found with tag '{tag}'.")
        return
    for k in keys:
        click.echo(k)
