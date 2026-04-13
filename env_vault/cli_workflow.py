"""CLI commands for vault workflows."""
from __future__ import annotations

import json

import click

from .storage import load_vault, save_vault, vault_exists
from .workflow import (
    DEFAULT_REGISTRY,
    WorkflowError,
    build_workflow,
    run_workflow,
)


@click.group("workflow")
def workflow_cmd() -> None:
    """Run ordered operation workflows on a vault."""


@workflow_cmd.command("run")
@click.argument("vault_name")
@click.argument("steps", nargs=-1, required=True)
@click.option("--password", prompt=True, hide_input=True, help="Vault password")
@click.option("--no-stop", is_flag=True, default=False, help="Continue on step errors")
@click.option("--dry-run", is_flag=True, default=False, help="Preview without saving")
def workflow_run(
    vault_name: str,
    steps: tuple,
    password: str,
    no_stop: bool,
    dry_run: bool,
) -> None:
    """Run STEPS workflow on VAULT_NAME."""
    if not vault_exists(vault_name):
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")
    try:
        step_list = build_workflow(list(steps), DEFAULT_REGISTRY)
    except WorkflowError as exc:
        raise click.ClickException(str(exc)) from exc

    vars_ = load_vault(vault_name, password)
    result = run_workflow(vars_, step_list, stop_on_error=not no_stop)

    if not result.success:
        for err in result.errors:
            click.echo(f"[error] {err}", err=True)
        raise click.ClickException("Workflow completed with errors.")

    click.echo(f"Steps run: {', '.join(result.steps_run)}")
    if dry_run:
        click.echo("[dry-run] Changes not saved.")
    else:
        save_vault(vault_name, password, result.vars_after)
        click.echo(f"Vault '{vault_name}' updated.")


@workflow_cmd.command("list")
def workflow_list() -> None:
    """List available workflow steps."""
    for name, step in DEFAULT_REGISTRY.items():
        click.echo(f"{name:25s}  {step.description}")
