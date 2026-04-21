"""CLI commands for vault inheritance."""
from __future__ import annotations

import json

import click

from env_vault.inherit import InheritError, inherit_all, resolve_inherited
from env_vault.storage import load_vault, vault_exists


@click.group("inherit")
def inherit_cmd() -> None:
    """Resolve variables via vault inheritance chains."""


@inherit_cmd.command("resolve")
@click.argument("key")
@click.option(
    "--vault",
    "vaults",
    multiple=True,
    required=True,
    help="Vault names in child-first order (repeatable).",
)
@click.option("--password", prompt=True, hide_input=True)
@click.option("--json", "as_json", is_flag=True, default=False)
def inherit_resolve(
    key: str, vaults: tuple, password: str, as_json: bool
) -> None:
    """Find the first vault in the chain that defines KEY."""
    try:
        result = resolve_inherited(
            key, list(vaults), load_vault, vault_exists, password
        )
    except InheritError as exc:
        raise click.ClickException(str(exc)) from exc

    if as_json:
        click.echo(
            json.dumps(
                {
                    "key": result.key,
                    "value": result.value,
                    "source_vault": result.source_vault,
                    "depth": result.depth,
                }
            )
        )
    else:
        click.echo(
            f"{result.key}={result.value}  "
            f"(from '{result.source_vault}', depth {result.depth})"
        )


@inherit_cmd.command("show")
@click.option(
    "--vault",
    "vaults",
    multiple=True,
    required=True,
    help="Vault names in child-first order (repeatable).",
)
@click.option("--password", prompt=True, hide_input=True)
@click.option("--json", "as_json", is_flag=True, default=False)
def inherit_show(vaults: tuple, password: str, as_json: bool) -> None:
    """Show merged variables from the full inheritance chain."""
    try:
        merged = inherit_all(list(vaults), load_vault, vault_exists, password)
    except InheritError as exc:
        raise click.ClickException(str(exc)) from exc

    if as_json:
        click.echo(
            json.dumps(
                {
                    k: {"value": r.value, "source": r.source_vault, "depth": r.depth}
                    for k, r in sorted(merged.items())
                }
            )
        )
    else:
        for k, r in sorted(merged.items()):
            click.echo(f"{k}={r.value}  (from '{r.source_vault}', depth {r.depth})")
