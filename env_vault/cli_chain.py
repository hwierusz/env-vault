"""CLI commands for variable chaining across vaults."""

from __future__ import annotations

import click

from env_vault.chain import ChainError, chain_sources, resolve_chain
from env_vault.storage import load_vault, vault_exists


@click.group("chain")
def chain_cmd() -> None:
    """Resolve variables across an ordered chain of vaults."""


@chain_cmd.command("resolve")
@click.argument("key")
@click.argument("vaults", nargs=-1, required=True)
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
def chain_resolve(key: str, vaults: tuple, password: str) -> None:
    """Look up KEY in VAULTS (ordered, first-wins) and print the value."""
    vault_list = list(vaults)

    def _load(name: str):
        return load_vault(name, password)

    def _exists(name: str) -> bool:
        return vault_exists(name)

    try:
        result = resolve_chain(key, vault_list, _load, _exists)
    except ChainError as exc:
        raise click.ClickException(str(exc))

    click.echo(f"{result.value}  # from {result.source}")


@chain_cmd.command("show")
@click.argument("vaults", nargs=-1, required=True)
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
def chain_show(vaults: tuple, password: str) -> None:
    """Print merged variables from VAULTS with first-wins precedence."""
    vault_list = list(vaults)

    def _load(name: str):
        return load_vault(name, password)

    def _exists(name: str) -> bool:
        return vault_exists(name)

    try:
        merged = chain_sources(vault_list, _load, _exists)
    except ChainError as exc:
        raise click.ClickException(str(exc))

    if not merged:
        click.echo("(no variables found)")
        return

    for k, v in sorted(merged.items()):
        click.echo(f"{k}={v}")
