"""CLI commands for variable dependency management."""
import click
from env_vault.storage import load_vault, save_vault, vault_exists
from env_vault import dependency as dep_mod


@click.group("dep")
def dep_cmd():
    """Manage variable dependencies."""


@dep_cmd.command("add")
@click.argument("vault")
@click.argument("key")
@click.argument("depends_on")
@click.password_option("--password", "-p", prompt=True)
def dep_add(vault: str, key: str, depends_on: str, password: str):
    """Record that KEY depends on DEPENDS_ON in VAULT."""
    if not vault_exists(vault):
        click.echo(f"Error: vault '{vault}' does not exist.", err=True)
        raise SystemExit(1)
    data = load_vault(vault, password)
    try:
        dep_mod.add_dependency(data, key, depends_on)
        save_vault(vault, password, data)
        click.echo(f"Dependency '{key}' -> '{depends_on}' added.")
    except dep_mod.DependencyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@dep_cmd.command("remove")
@click.argument("vault")
@click.argument("key")
@click.argument("depends_on")
@click.password_option("--password", "-p", prompt=True)
def dep_remove(vault: str, key: str, depends_on: str, password: str):
    """Remove a dependency from VAULT."""
    if not vault_exists(vault):
        click.echo(f"Error: vault '{vault}' does not exist.", err=True)
        raise SystemExit(1)
    data = load_vault(vault, password)
    try:
        dep_mod.remove_dependency(data, key, depends_on)
        save_vault(vault, password, data)
        click.echo(f"Dependency '{key}' -> '{depends_on}' removed.")
    except dep_mod.DependencyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@dep_cmd.command("list")
@click.argument("vault")
@click.argument("key")
@click.password_option("--password", "-p", prompt=True)
def dep_list(vault: str, key: str, password: str):
    """List dependencies of KEY in VAULT."""
    if not vault_exists(vault):
        click.echo(f"Error: vault '{vault}' does not exist.", err=True)
        raise SystemExit(1)
    data = load_vault(vault, password)
    deps = dep_mod.list_dependencies(data, key)
    if deps:
        for d in deps:
            click.echo(d)
    else:
        click.echo(f"No dependencies for '{key}'.")


@dep_cmd.command("order")
@click.argument("vault")
@click.password_option("--password", "-p", prompt=True)
def dep_order(vault: str, password: str):
    """Print topologically-sorted variable order for VAULT."""
    if not vault_exists(vault):
        click.echo(f"Error: vault '{vault}' does not exist.", err=True)
        raise SystemExit(1)
    data = load_vault(vault, password)
    try:
        order = dep_mod.resolve_order(data)
        for item in order:
            click.echo(item)
    except dep_mod.DependencyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
