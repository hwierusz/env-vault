"""CLI commands for vault signing and verification."""
from __future__ import annotations

import click

from .signature import SignatureError, attach_signature, check_signature
from .storage import load_vault, save_vault, vault_exists


@click.group("signature")
def signature_cmd() -> None:
    """Sign and verify vault contents."""


@signature_cmd.command("sign")
@click.argument("vault_name")
@click.option("--secret", required=True, envvar="VAULT_SIGN_SECRET", help="HMAC secret")
@click.option("--password", required=True, envvar="VAULT_PASSWORD", help="Vault password")
def sig_sign(vault_name: str, secret: str, password: str) -> None:
    """Attach an HMAC signature to VAULT_NAME."""
    if not vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' does not exist.", err=True)
        raise SystemExit(1)
    try:
        data = load_vault(vault_name, password)
        signed = attach_signature(data, secret)
        save_vault(vault_name, password, signed)
        click.echo(f"Vault '{vault_name}' signed successfully.")
    except SignatureError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@signature_cmd.command("verify")
@click.argument("vault_name")
@click.option("--secret", required=True, envvar="VAULT_SIGN_SECRET", help="HMAC secret")
@click.option("--password", required=True, envvar="VAULT_PASSWORD", help="Vault password")
def sig_verify(vault_name: str, secret: str, password: str) -> None:
    """Verify the HMAC signature of VAULT_NAME."""
    if not vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' does not exist.", err=True)
        raise SystemExit(1)
    try:
        data = load_vault(vault_name, password)
        valid = check_signature(data, secret)
        if valid:
            click.echo(f"Signature valid for vault '{vault_name}'.")
        else:
            click.echo(f"Signature INVALID for vault '{vault_name}'.", err=True)
            raise SystemExit(2)
    except SignatureError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
