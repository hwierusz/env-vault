"""CLI commands for the annotation feature."""

from __future__ import annotations

import click

from env_vault.annotate import (
    AnnotateError,
    get_annotation,
    list_annotations,
    remove_annotation,
    set_annotation,
)
from env_vault.storage import load_vault, save_vault


@click.group("annotate")
def annotate_cmd():
    """Manage annotations (notes) attached to vault keys."""


@annotate_cmd.command("set")
@click.argument("vault")
@click.argument("key")
@click.argument("note")
def annotate_set(vault: str, key: str, note: str):
    """Attach NOTE to KEY in VAULT."""
    try:
        set_annotation(vault, key, note, load_vault, save_vault)
        click.echo(f"Annotation set for '{key}'.")
    except AnnotateError as exc:
        raise click.ClickException(str(exc))


@annotate_cmd.command("get")
@click.argument("vault")
@click.argument("key")
def annotate_get(vault: str, key: str):
    """Print the annotation for KEY in VAULT."""
    try:
        note = get_annotation(vault, key, load_vault)
    except Exception as exc:
        raise click.ClickException(str(exc))
    if note is None:
        click.echo(f"No annotation for '{key}'.")
    else:
        click.echo(note)


@annotate_cmd.command("remove")
@click.argument("vault")
@click.argument("key")
def annotate_remove(vault: str, key: str):
    """Remove the annotation for KEY in VAULT."""
    try:
        remove_annotation(vault, key, load_vault, save_vault)
        click.echo(f"Annotation removed for '{key}'.")
    except AnnotateError as exc:
        raise click.ClickException(str(exc))


@annotate_cmd.command("list")
@click.argument("vault")
def annotate_list(vault: str):
    """List all annotated keys in VAULT."""
    try:
        annotations = list_annotations(vault, load_vault)
    except Exception as exc:
        raise click.ClickException(str(exc))
    if not annotations:
        click.echo("No annotations found.")
        return
    for key, note in sorted(annotations.items()):
        click.echo(f"{key}: {note}")
