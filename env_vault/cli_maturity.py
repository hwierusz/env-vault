"""CLI commands for vault maturity assessment."""
import json
import click
from env_vault.maturity import assess_maturity, MaturityError, LEVELS


@click.group("maturity")
def maturity_cmd():
    """Assess vault maturity level."""


@maturity_cmd.command("show")
@click.argument("vault_name")
@click.option("--password", prompt=True, hide_input=True)
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def maturity_show(vault_name: str, password: str, fmt: str):
    """Show maturity report for a vault."""
    try:
        report = assess_maturity(vault_name, password)
    except MaturityError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    if fmt == "json":
        click.echo(json.dumps({
            "vault": report.vault_name,
            "overall": report.overall,
            "level": report.level,
            "scores": report.scores,
        }, indent=2))
        return

    click.echo(f"Vault : {report.vault_name}")
    click.echo(f"Level : {report.level.upper()} (score {report.overall}/100)")
    click.echo("")
    click.echo("Dimension scores:")
    for dim, score in report.scores.items():
        bar = "#" * (score // 10) + "-" * (10 - score // 10)
        click.echo(f"  {dim:<20} [{bar}] {score}")


@maturity_cmd.command("levels")
def maturity_levels():
    """List all maturity levels."""
    for i, lvl in enumerate(LEVELS):
        click.echo(f"  {i}  {lvl}")
