"""CLI commands for namespace management."""

import click
from env_vault.namespace import (
    assign_to_namespace,
    remove_from_namespace,
    list_namespaces,
    get_namespace_vars,
    NamespaceError,
)
from env_vault.storage import load_vault, save_vault


@click.group(name="namespace")
def namespace_cmd():
    """Manage variable namespaces within a vault."""


@namespace_cmd.command("assign")
@click.argument("vault")
@click.argument("key")
@click.argument("namespace")
@click.password_option(prompt="Vault password")
def ns_assign(vault, key, namespace, password):
    """Assign KEY in VAULT to NAMESPACE."""
    try:
        assign_to_namespace(vault, key, namespace, load_vault, save_vault, password)
        click.echo(f"Assigned '{key}' to namespace '{namespace}'.")
    except NamespaceError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@namespace_cmd.command("remove")
@click.argument("vault")
@click.argument("key")
@click.argument("namespace")
@click.password_option(prompt="Vault password")
def ns_remove(vault, key, namespace, password):
    """Remove KEY from NAMESPACE in VAULT."""
    try:
        remove_from_namespace(vault, key, namespace, load_vault, save_vault, password)
        click.echo(f"Removed '{key}' from namespace '{namespace}'.")
    except NamespaceError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@namespace_cmd.command("list")
@click.argument("vault")
@click.password_option(prompt="Vault password")
def ns_list(vault, password):
    """List all namespaces in VAULT."""
    try:
        namespaces = list_namespaces(vault, load_vault, password)
        if not namespaces:
            click.echo("No namespaces defined.")
            return
        for ns, keys in sorted(namespaces.items()):
            click.echo(f"{ns}: {', '.join(keys)}")
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@namespace_cmd.command("show")
@click.argument("vault")
@click.argument("namespace")
@click.password_option(prompt="Vault password")
def ns_show(vault, namespace, password):
    """Show all key=value pairs in NAMESPACE within VAULT."""
    try:
        vars_ = get_namespace_vars(vault, namespace, load_vault, password)
        if not vars_:
            click.echo(f"Namespace '{namespace}' is empty.")
            return
        for k, v in sorted(vars_.items()):
            click.echo(f"{k}={v}")
    except NamespaceError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
