"""CLI commands for vault backup and restore."""

import click

from env_vault.backup import BackupError, create_backup, restore_backup


@click.group("backup")
def backup_cmd():
    """Backup and restore vaults."""


@backup_cmd.command("create")
@click.argument("vault_name")
@click.argument("dest")
@click.password_option("--password", "-p", prompt="Vault password", help="Vault password")
def backup_create(vault_name: str, dest: str, password: str):
    """Create an encrypted backup of VAULT_NAME at DEST."""
    try:
        path = create_backup(vault_name, password, dest)
        click.echo(f"Backup written to {path}")
    except BackupError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@backup_cmd.command("restore")
@click.argument("src")
@click.option(
    "--vault",
    "-v",
    default=None,
    help="Override target vault name (default: name stored in backup).",
)
@click.password_option("--password", "-p", prompt="Backup password", help="Backup password")
def backup_restore(src: str, vault: str | None, password: str):
    """Restore an encrypted backup from SRC."""
    try:
        target = restore_backup(src, password, vault_name=vault)
        click.echo(f"Restored into vault '{target}'.")
    except BackupError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
