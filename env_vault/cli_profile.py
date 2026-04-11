"""CLI commands for profile management."""

import click

from env_vault.profile import (
    ProfileError,
    delete_profile,
    get_profile,
    get_profile_var,
    list_profiles,
    set_profile_var,
)


@click.group("profile")
def profile_cmd():
    """Manage named variable profiles within a vault."""


@profile_cmd.command("list")
@click.argument("vault")
@click.password_option("--password", "-p", prompt="Vault password", help="Vault password.")
def profile_list(vault: str, password: str):
    """List all profiles in VAULT."""
    try:
        profiles = list_profiles(vault, password)
    except Exception as exc:
        raise click.ClickException(str(exc))
    if not profiles:
        click.echo("No profiles found.")
    else:
        for name in profiles:
            click.echo(name)


@profile_cmd.command("set")
@click.argument("vault")
@click.argument("profile")
@click.argument("key")
@click.argument("value")
@click.password_option("--password", "-p", prompt="Vault password", help="Vault password.")
def profile_set(vault: str, profile: str, key: str, value: str, password: str):
    """Set KEY=VALUE inside PROFILE of VAULT."""
    try:
        set_profile_var(vault, password, profile, key, value)
    except ProfileError as exc:
        raise click.ClickException(str(exc))
    click.echo(f"[{profile}] {key} set.")


@profile_cmd.command("get")
@click.argument("vault")
@click.argument("profile")
@click.argument("key")
@click.password_option("--password", "-p", prompt="Vault password", help="Vault password.")
def profile_get(vault: str, profile: str, key: str, password: str):
    """Get KEY from PROFILE of VAULT."""
    try:
        value = get_profile_var(vault, password, profile, key)
    except Exception as exc:
        raise click.ClickException(str(exc))
    if value is None:
        raise click.ClickException(f"Key '{key}' not found in profile '{profile}'.")
    click.echo(value)


@profile_cmd.command("show")
@click.argument("vault")
@click.argument("profile")
@click.password_option("--password", "-p", prompt="Vault password", help="Vault password.")
def profile_show(vault: str, profile: str, password: str):
    """Show all variables in PROFILE of VAULT."""
    try:
        vars_ = get_profile(vault, password, profile)
    except ProfileError as exc:
        raise click.ClickException(str(exc))
    for k, v in sorted(vars_.items()):
        click.echo(f"{k}={v}")


@profile_cmd.command("delete")
@click.argument("vault")
@click.argument("profile")
@click.password_option("--password", "-p", prompt="Vault password", help="Vault password.")
def profile_delete(vault: str, profile: str, password: str):
    """Delete PROFILE from VAULT."""
    try:
        count = delete_profile(vault, password, profile)
    except ProfileError as exc:
        raise click.ClickException(str(exc))
    click.echo(f"Profile '{profile}' deleted ({count} variable(s) removed).")
