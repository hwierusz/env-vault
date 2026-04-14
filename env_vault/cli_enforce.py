"""CLI commands for policy enforcement."""
from __future__ import annotations

import json
import sys

import click

from env_vault.enforce import EnforceError, available_policies, enforce_policy
from env_vault.storage import load_vault, vault_exists


@click.group("enforce")
def enforce_cmd() -> None:
    """Enforce policies on vault variables."""


@enforce_cmd.command("run")
@click.argument("vault_name")
@click.argument("password")
@click.option(
    "--policy",
    "policies",
    multiple=True,
    default=["no_empty_values", "uppercase_keys", "no_spaces_in_keys"],
    show_default=True,
    help="Policy to apply (repeatable).",
)
@click.option("--json", "as_json", is_flag=True, help="Output results as JSON.")
def enforce_run(
    vault_name: str, password: str, policies: tuple, as_json: bool
) -> None:
    """Run policies against VAULT_NAME and report violations."""
    if not vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' does not exist.", err=True)
        sys.exit(1)

    try:
        data = load_vault(vault_name, password)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error loading vault: {exc}", err=True)
        sys.exit(1)

    vars_ = {k: v for k, v in data.items() if not k.startswith("_")}

    try:
        violations = enforce_policy(vars_, list(policies))
    except EnforceError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if as_json:
        click.echo(
            json.dumps(
                [{"key": v.key, "policy": v.policy, "message": v.message} for v in violations],
                indent=2,
            )
        )
    else:
        if not violations:
            click.echo("All policies passed.")
        else:
            for v in violations:
                click.echo(f"[{v.policy}] {v.key}: {v.message}")
            sys.exit(1)


@enforce_cmd.command("policies")
def list_policies() -> None:
    """List all available built-in policies."""
    for name in available_policies():
        click.echo(name)
