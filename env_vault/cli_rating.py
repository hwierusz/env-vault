"""CLI commands for vault rating."""

from __future__ import annotations

import json
import sys

import click

from env_vault.rating import rate_vault, RatingError
from env_vault.storage import vault_exists


@click.group("rating")
def rating_cmd() -> None:
    """Vault quality rating commands."""


@rating_cmd.command("show")
@click.argument("vault_name")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output format.",
)
def rating_show(vault_name: str, password: str, fmt: str) -> None:
    """Show the letter-grade rating for VAULT_NAME."""
    if not vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' does not exist.", err=True)
        sys.exit(1)

    try:
        result = rate_vault(vault_name, password)
    except RatingError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if fmt == "json":
        click.echo(
            json.dumps(
                {
                    "vault": vault_name,
                    "grade": result.grade,
                    "score": result.score,
                    "findings": result.findings,
                    "summary": result.summary,
                },
                indent=2,
            )
        )
    else:
        click.echo(f"Vault : {vault_name}")
        click.echo(f"Grade : {result.grade}")
        click.echo(f"Score : {result.score}/100")
        click.echo(f"Lint  : {result.findings} finding(s)")
        click.echo(f"Note  : {result.summary}")
