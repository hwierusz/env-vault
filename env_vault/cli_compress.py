"""CLI commands for compressing and decompressing vault files."""

import os
import click

from .compress import compress_vault, decompress_vault, compression_ratio, CompressError
from .storage import load_vault, vault_exists


@click.group("compress")
def compress_cmd() -> None:
    """Compress or decompress vault archives."""


@compress_cmd.command("pack")
@click.argument("vault_name")
@click.argument("output_path")
@click.password_option(prompt="Vault password", confirmation_prompt=False)
def pack(vault_name: str, output_path: str, password: str) -> None:
    """Compress VAULT_NAME into a binary archive at OUTPUT_PATH."""
    if not vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' does not exist.", err=True)
        raise SystemExit(1)
    try:
        data = load_vault(vault_name, password)
        blob = compress_vault(data)
        with open(output_path, "wb") as fh:
            fh.write(blob)
        ratio = compression_ratio(data)
        click.echo(
            f"Packed '{vault_name}' → {output_path}  "
            f"(ratio {ratio:.2%})"
        )
    except CompressError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@compress_cmd.command("unpack")
@click.argument("archive_path")
@click.option("--show", is_flag=True, help="Print decompressed JSON to stdout.")
def unpack(archive_path: str, show: bool) -> None:
    """Decompress an archive created by 'pack' and display its contents."""
    if not os.path.isfile(archive_path):
        click.echo(f"Error: file '{archive_path}' not found.", err=True)
        raise SystemExit(1)
    try:
        with open(archive_path, "rb") as fh:
            blob = fh.read()
        data = decompress_vault(blob)
    except CompressError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    if show:
        import json
        click.echo(json.dumps(data, indent=2))
    else:
        var_count = len(data.get("vars", {}))
        click.echo(
            f"Archive '{archive_path}' contains {var_count} variable(s)."
        )
