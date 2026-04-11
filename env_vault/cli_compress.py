import click
from env_vault.storage import load_vault, save_vault, vault_exists
from env_vault.compress import compress_vault, decompress_vault, compression_ratio, CompressError
import os


@click.group(name="compress")
def compress_cmd():
    """Pack and unpack vault data using gzip compression."""


@compress_cmd.command("pack")
@click.argument("vault_name")
@click.argument("output_file")
@click.password_option(prompt="Vault password", confirmation_prompt=False)
def pack(vault_name: str, output_file: str, password: str):
    """Compress VAULT_NAME into OUTPUT_FILE."""
    if not vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' does not exist.", err=True)
        raise SystemExit(1)
    try:
        variables = load_vault(vault_name, password)
        data = compress_vault(variables)
        with open(output_file, "wb") as fh:
            fh.write(data)
        ratio = compression_ratio(variables)
        click.echo(
            f"Packed {len(variables)} variable(s) into '{output_file}' "
            f"(ratio: {ratio:.2f})."
        )
    except CompressError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@compress_cmd.command("unpack")
@click.argument("input_file")
@click.argument("vault_name")
@click.password_option(prompt="Vault password", confirmation_prompt=False)
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing vault.")
def unpack(input_file: str, vault_name: str, password: str, overwrite: bool):
    """Decompress INPUT_FILE and store into VAULT_NAME."""
    if vault_exists(vault_name) and not overwrite:
        click.echo(
            f"Error: vault '{vault_name}' already exists. Use --overwrite to replace it.",
            err=True,
        )
        raise SystemExit(1)
    if not os.path.isfile(input_file):
        click.echo(f"Error: file '{input_file}' not found.", err=True)
        raise SystemExit(1)
    try:
        with open(input_file, "rb") as fh:
            data = fh.read()
        variables = decompress_vault(data)
        save_vault(vault_name, password, variables)
        click.echo(f"Unpacked {len(variables)} variable(s) into vault '{vault_name}'.")
    except CompressError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
