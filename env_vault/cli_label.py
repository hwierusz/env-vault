"""CLI commands for label management."""

from __future__ import annotations

import click

from env_vault.label import LabelError, add_label, find_by_label, list_labels, remove_label
from env_vault.storage import load_vault, save_vault, vault_exists


@click.group("label")
def label_cmd() -> None:
    """Manage labels attached to vault variables."""


@label_cmd.command("add")
@click.argument("vault_name")
@click.argument("key")
@click.argument("label")
def label_add(vault_name: str, key: str, label: str) -> None:
    """Attach LABEL to KEY in VAULT_NAME."""
    if not vault_exists(vault_name):
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")
    try:
        add_label(vault_name, key, label, load_vault, save_vault)
        click.echo(f"Label '{label}' added to '{key}'.")
    except LabelError as exc:
        raise click.ClickException(str(exc)) from exc


@label_cmd.command("remove")
@click.argument("vault_name")
@click.argument("key")
@click.argument("label")
def label_remove(vault_name: str, key: str, label: str) -> None:
    """Detach LABEL from KEY in VAULT_NAME."""
    if not vault_exists(vault_name):
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")
    remove_label(vault_name, key, label, load_vault, save_vault)
    click.echo(f"Label '{label}' removed from '{key}'.")


@label_cmd.command("list")
@click.argument("vault_name")
@click.argument("key")
def label_list(vault_name: str, key: str) -> None:
    """List all labels on KEY in VAULT_NAME."""
    if not vault_exists(vault_name):
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")
    labels = list_labels(vault_name, key, load_vault)
    if labels:
        for lbl in labels:
            click.echo(lbl)
    else:
        click.echo("No labels.")


@label_cmd.command("find")
@click.argument("vault_name")
@click.argument("label")
def label_find(vault_name: str, label: str) -> None:
    """Find all keys carrying LABEL in VAULT_NAME."""
    if not vault_exists(vault_name):
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")
    matches = find_by_label(vault_name, label, load_vault)
    if matches:
        for key, lbls in matches.items():
            click.echo(f"{key}: {', '.join(lbls)}")
    else:
        click.echo(f"No keys found with label '{label}'.")
