"""CLI commands for copying variables between vaults."""

import click
from env_vault.copy import copy_vars, CopyError


@click.command("copy")
@click.argument("src_vault")
@click.argument("dst_vault")
@click.option("--src-password", prompt=True, hide_input=True, help="Source vault password.")
@click.option("--dst-password", prompt=True, hide_input=True, help="Destination vault password.")
@click.option(
    "--key",
    "keys",
    multiple=True,
    default=None,
    help="Key(s) to copy. Repeat for multiple. Omit to copy all.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite existing keys in the destination vault.",
)
def copy_cmd(src_vault, dst_vault, src_password, dst_password, keys, overwrite):
    """Copy variables from SRC_VAULT to DST_VAULT.

    Copies all variables by default. Use --key to select specific variables.
    """
    try:
        count = copy_vars(
            src_vault=src_vault,
            dst_vault=dst_vault,
            src_password=src_password,
            dst_password=dst_password,
            keys=list(keys) if keys else None,
            overwrite=overwrite,
        )
        click.echo(f"Copied {count} variable(s) from '{src_vault}' to '{dst_vault}'.")
    except CopyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
