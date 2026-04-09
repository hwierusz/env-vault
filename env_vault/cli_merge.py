"""CLI commands for merging vaults."""

import click
from env_vault.merge import merge_vaults, MergeError


@click.command("merge")
@click.argument("src")
@click.argument("dst")
@click.option("--src-password", prompt="Source vault password", hide_input=True,
              help="Password for the source vault.")
@click.option("--dst-password", prompt="Destination vault password", hide_input=True,
              help="Password for the destination vault.")
@click.option("--overwrite", is_flag=True, default=False,
              help="Overwrite existing keys in destination vault.")
@click.option("--key", "keys", multiple=True,
              help="Specific key(s) to merge. Can be repeated.")
def merge_cmd(src, dst, src_password, dst_password, overwrite, keys):
    """Merge variables from SRC vault into DST vault.

    By default, keys that already exist in DST are skipped.
    Use --overwrite to replace them.
    """
    try:
        result = merge_vaults(
            src_name=src,
            src_password=src_password,
            dst_name=dst,
            dst_password=dst_password,
            overwrite=overwrite,
            keys=list(keys) if keys else None,
        )
    except MergeError as exc:
        raise click.ClickException(str(exc))

    added = result["added"]
    skipped = result["skipped"]

    if added:
        click.echo(f"Merged {len(added)} variable(s) into '{dst}': {', '.join(added)}")
    else:
        click.echo(f"No variables were added to '{dst}'.")

    if skipped:
        click.echo(
            f"Skipped {len(skipped)} existing variable(s) (use --overwrite to replace): "
            + ", ".join(skipped)
        )
