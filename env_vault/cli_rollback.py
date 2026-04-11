"""CLI commands for vault rollback."""

from __future__ import annotations

import click

from env_vault.rollback import list_rollback_points, rollback_to, RollbackError
from env_vault.storage import load_vault, save_vault


@click.group(name="rollback")
def rollback_cmd() -> None:
    """Rollback a vault to a previous state."""


@rollback_cmd.command("list")
@click.argument("vault_name")
@click.option("--vault-dir", default=".", show_default=True)
def rollback_list(vault_name: str, vault_dir: str) -> None:
    """List available rollback points for VAULT_NAME."""
    try:
        points = list_rollback_points(vault_name, vault_dir=vault_dir)
    except RollbackError as exc:
        raise click.ClickException(str(exc))

    if not points:
        click.echo("No history entries found.")
        return

    click.echo(f"{'#':<5} {'timestamp':<26} {'action':<8} key")
    click.echo("-" * 55)
    for p in points:
        ts = p.get("timestamp", "")
        action = p.get("action", "")
        key = p.get("key", "")
        click.echo(f"{p['index']:<5} {ts:<26} {action:<8} {key}")


@rollback_cmd.command("apply")
@click.argument("vault_name")
@click.argument("index", type=int)
@click.option("--vault-dir", default=".", show_default=True)
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
def rollback_apply(vault_name: str, index: int, vault_dir: str, yes: bool) -> None:
    """Revert VAULT_NAME to the state at history INDEX."""
    if not yes:
        click.confirm(
            f"Revert '{vault_name}' to history index {index}? This overwrites current data.",
            abort=True,
        )

    try:
        state = rollback_to(
            vault_name,
            index,
            load_fn=lambda name: load_vault(name, vault_dir=vault_dir),
            save_fn=lambda name, data: save_vault(name, data, vault_dir=vault_dir),
            vault_dir=vault_dir,
        )
    except RollbackError as exc:
        raise click.ClickException(str(exc))

    click.echo(
        f"Vault '{vault_name}' rolled back to index {index} ({len(state)} variable(s))."
    )
