"""CLI commands for vault variable trend analysis."""
import json

import click

from env_vault.trend import TrendEntry, TrendError, trend_vault
from env_vault.storage import vault_exists


@click.group("trend")
def trend_cmd() -> None:
    """Analyse activity trends for vault variables."""


@trend_cmd.command("show")
@click.argument("vault")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
@click.option("--top", default=10, show_default=True, help="Limit output to N entries.")
def trend_show(vault: str, fmt: str, top: int) -> None:
    """Show activity trend for variables in VAULT."""
    if not vault_exists(vault):
        click.echo(f"Error: vault '{vault}' does not exist.", err=True)
        raise SystemExit(1)

    try:
        entries = trend_vault(vault)
    except TrendError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    if not entries:
        click.echo("No audit events found.")
        return

    limited = entries[:top]

    if fmt == "json":
        data = [
            {
                "key": e.key,
                "total_reads": e.total_reads,
                "total_writes": e.total_writes,
                "total_deletes": e.total_deletes,
                "activity_score": e.activity_score,
                "last_action": e.last_action,
                "last_timestamp": e.last_timestamp,
            }
            for e in limited
        ]
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"{'KEY':<30} {'READS':>6} {'WRITES':>7} {'DELETES':>8} {'SCORE':>6}")
        click.echo("-" * 62)
        for e in limited:
            click.echo(
                f"{e.key:<30} {e.total_reads:>6} {e.total_writes:>7} "
                f"{e.total_deletes:>8} {e.activity_score:>6}"
            )
