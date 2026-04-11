"""CLI commands for variable classification."""

from __future__ import annotations

import json

import click

from .classify import ClassifyError, classify_vars, summary
from .storage import load_vault


@click.group("classify")
def classify_cmd() -> None:
    """Classify vault variables by sensitivity."""


@classify_cmd.command("run")
@click.argument("vault_name")
@click.argument("password")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text", show_default=True)
@click.option("--category", default=None, help="Filter output to a specific category.")
def classify_run(vault_name: str, password: str, fmt: str, category: str | None) -> None:
    """Classify all variables in VAULT_NAME."""
    try:
        data = load_vault(vault_name, password)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    vars_dict = {k: v for k, v in data.items() if not k.startswith("_")}

    try:
        results = classify_vars(vars_dict)
    except ClassifyError as exc:
        raise click.ClickException(str(exc)) from exc

    if category:
        results = [r for r in results if r.category == category]

    if fmt == "json":
        click.echo(json.dumps([{"key": r.key, "category": r.category, "confidence": r.confidence} for r in results], indent=2))
        return

    if not results:
        click.echo("No variables match.")
        return

    col = 32
    click.echo(f"{'KEY':<{col}} {'CATEGORY':<10} CONFIDENCE")
    click.echo("-" * (col + 22))
    for r in results:
        click.echo(f"{r.key:<{col}} {r.category:<10} {r.confidence:.0%}")


@classify_cmd.command("summary")
@click.argument("vault_name")
@click.argument("password")
def classify_summary(vault_name: str, password: str) -> None:
    """Print a category count summary for VAULT_NAME."""
    try:
        data = load_vault(vault_name, password)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    vars_dict = {k: v for k, v in data.items() if not k.startswith("_")}
    results = classify_vars(vars_dict)
    counts = summary(results)

    if not counts:
        click.echo("Vault is empty.")
        return

    for cat, n in sorted(counts.items()):
        click.echo(f"{cat:<12} {n}")
