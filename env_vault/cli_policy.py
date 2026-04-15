"""CLI commands for policy management."""
import json
import sys

import click

from env_vault.policy import (
    PolicyError,
    assign_policy,
    unassign_policy,
    list_policies_for,
    evaluate_policies,
)
from env_vault.storage import load_vault, save_vault, vault_exists


@click.group("policy")
def policy_cmd():
    """Manage and evaluate policies on vaults."""


def _require_vault(name: str) -> dict:
    if not vault_exists(name):
        click.echo(f"Error: vault '{name}' does not exist.", err=True)
        sys.exit(1)
    return load_vault(name)


@policy_cmd.command("assign")
@click.argument("vault")
@click.argument("policy")
@click.password_option(prompt="Vault password")
def policy_assign(vault: str, policy: str, password: str):
    """Assign POLICY to VAULT."""
    data = _require_vault(vault)
    try:
        assign_policy(data, vault, policy)
    except PolicyError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    save_vault(vault, data, password)
    click.echo(f"Policy '{policy}' assigned to vault '{vault}'.")


@policy_cmd.command("unassign")
@click.argument("vault")
@click.argument("policy")
@click.password_option(prompt="Vault password")
def policy_unassign(vault: str, policy: str, password: str):
    """Remove POLICY from VAULT."""
    data = _require_vault(vault)
    try:
        unassign_policy(data, vault, policy)
    except PolicyError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    save_vault(vault, data, password)
    click.echo(f"Policy '{policy}' removed from vault '{vault}'.")


@policy_cmd.command("list")
@click.argument("vault")
@click.password_option(prompt="Vault password")
def policy_list(vault: str, password: str):
    """List policies assigned to VAULT."""
    data = _require_vault(vault)
    policies = list_policies_for(data, vault)
    if not policies:
        click.echo("No policies assigned.")
    else:
        for p in policies:
            click.echo(p)


@policy_cmd.command("evaluate")
@click.argument("vault")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.password_option(prompt="Vault password")
def policy_evaluate(vault: str, as_json: bool, password: str):
    """Evaluate all assigned policies against VAULT."""
    data = _require_vault(vault)
    results = evaluate_policies(data, vault)
    if as_json:
        click.echo(json.dumps([{"policy": r.policy, "passed": r.passed, "violations": r.violations} for r in results], indent=2))
    else:
        for r in results:
            status = "PASS" if r.passed else "FAIL"
            click.echo(f"[{status}] {r.policy}")
            for v in r.violations:
                click.echo(f"  - {v}")
