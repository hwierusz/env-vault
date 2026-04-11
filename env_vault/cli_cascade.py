"""CLI commands for cascade variable resolution."""

import click
from env_vault.cascade import CascadeError, resolve_cascade, cascade_sources


@click.group(name="cascade")
def cascade_cmd():
    """Resolve env vars from multiple vaults in priority order."""


@cascade_cmd.command(name="resolve")
@click.argument("vaults", nargs=-1, required=True)
@click.option("--password", "-p", prompt=True, hide_input=True, help="Vault password.")
@click.option("--format", "fmt", default="dotenv", type=click.Choice(["dotenv", "json"]), show_default=True)
def cascade_resolve(vaults, password, fmt):
    """Merge variables from VAULTS (left-to-right, last wins) and print them."""
    try:
        merged = resolve_cascade(list(vaults), password)
    except CascadeError as exc:
        raise click.ClickException(str(exc))

    if fmt == "json":
        import json
        click.echo(json.dumps(merged, indent=2))
    else:
        for key, value in merged.items():
            click.echo(f"{key}={value}")


@cascade_cmd.command(name="sources")
@click.argument("vaults", nargs=-1, required=True)
@click.option("--password", "-p", prompt=True, hide_input=True, help="Vault password.")
def cascade_sources_cmd(vaults, password):
    """Show which vault last defines each variable across VAULTS."""
    try:
        sources = cascade_sources(list(vaults), password)
    except CascadeError as exc:
        raise click.ClickException(str(exc))

    if not sources:
        click.echo("No variables found.")
        return

    max_key = max(len(k) for k in sources)
    for key, vault_name in sorted(sources.items()):
        click.echo(f"{key:<{max_key}}  <- {vault_name}")
