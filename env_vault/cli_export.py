"""CLI commands for exporting and importing vault variables."""

import sys
import click

from env_vault.export import export_vars, import_vars, SUPPORTED_FORMATS
from env_vault.storage import load_vault, save_vault, vault_exists


@click.command("export")
@click.argument("project")
@click.option("--format", "fmt", default="dotenv", show_default=True,
              type=click.Choice(SUPPORTED_FORMATS), help="Output format.")
@click.option("--output", "-o", default=None, help="Write to file instead of stdout.")
@click.password_option("--password", prompt="Vault password", confirmation_prompt=False)
def export_cmd(project: str, fmt: str, output, password: str) -> None:
    """Export variables from PROJECT vault to stdout or a file."""
    if not vault_exists(project):
        click.echo(f"Error: vault '{project}' does not exist.", err=True)
        sys.exit(1)

    try:
        data = load_vault(project, password)
    except Exception:
        click.echo("Error: failed to decrypt vault. Wrong password?", err=True)
        sys.exit(1)

    content = export_vars(data, fmt=fmt)

    if output:
        with open(output, "w") as fh:
            fh.write(content + "\n")
        click.echo(f"Exported {len(data)} variable(s) to '{output}'.")
    else:
        click.echo(content)


@click.command("import")
@click.argument("project")
@click.argument("filepath", type=click.Path(exists=True, readable=True))
@click.option("--format", "fmt", default="dotenv", show_default=True,
              type=click.Choice(SUPPORTED_FORMATS), help="Input format.")
@click.option("--overwrite", is_flag=True, default=False,
              help="Overwrite existing keys without prompting.")
@click.password_option("--password", prompt="Vault password", confirmation_prompt=False)
def import_cmd(project: str, filepath: str, fmt: str, overwrite: bool, password: str) -> None:
    """Import variables from FILEPATH into PROJECT vault."""
    if not vault_exists(project):
        click.echo(f"Error: vault '{project}' does not exist.", err=True)
        sys.exit(1)

    try:
        existing = load_vault(project, password)
    except Exception:
        click.echo("Error: failed to decrypt vault. Wrong password?", err=True)
        sys.exit(1)

    with open(filepath) as fh:
        content = fh.read()

    try:
        incoming = import_vars(content, fmt=fmt)
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    conflicts = [k for k in incoming if k in existing]
    if conflicts and not overwrite:
        click.echo(f"Conflicting keys: {', '.join(conflicts)}")
        click.echo("Use --overwrite to replace existing values.")
        sys.exit(1)

    existing.update(incoming)
    save_vault(project, existing, password)
    click.echo(f"Imported {len(incoming)} variable(s) into vault '{project}'.")
