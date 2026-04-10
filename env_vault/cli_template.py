"""CLI commands for env-vault template rendering."""

import sys
import click

from env_vault.storage import load_vault, vault_exists
from env_vault.template import render_template, collect_placeholders, TemplateError


@click.group(name="template")
def template_cmd():
    """Render templates using variables stored in a vault."""


@template_cmd.command(name="render")
@click.argument("vault_name")
@click.argument("template_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.option(
    "--output", "-o",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Write rendered output to this file instead of stdout.",
)
@click.option(
    "--no-strict",
    is_flag=True,
    default=False,
    help="Leave unresolved placeholders as-is instead of raising an error.",
)
def template_render(vault_name, template_file, password, output, no_strict):
    """Render TEMPLATE_FILE substituting {{ KEY }} placeholders from VAULT_NAME."""
    if not vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' does not exist.", err=True)
        sys.exit(1)

    try:
        variables = load_vault(vault_name, password)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error: could not unlock vault — {exc}", err=True)
        sys.exit(1)

    with open(template_file, "r", encoding="utf-8") as fh:
        template_str = fh.read()

    try:
        rendered = render_template(template_str, variables, strict=not no_strict)
    except TemplateError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if output:
        with open(output, "w", encoding="utf-8") as fh:
            fh.write(rendered)
        click.echo(f"Rendered output written to {output}")
    else:
        click.echo(rendered, nl=False)


@template_cmd.command(name="inspect")
@click.argument("template_file", type=click.Path(exists=True, dir_okay=False))
def template_inspect(template_file):
    """List all {{ KEY }} placeholders found in TEMPLATE_FILE."""
    with open(template_file, "r", encoding="utf-8") as fh:
        template_str = fh.read()

    placeholders = collect_placeholders(template_str)
    if not placeholders:
        click.echo("No placeholders found.")
    else:
        click.echo(f"Found {len(placeholders)} placeholder(s):")
        for name in placeholders:
            click.echo(f"  {name}")
