"""CLI commands for token-based access management."""
import json
import click
from env_vault.storage import load_vault, save_vault, vault_exists
from env_vault.token import (
    TokenError,
    issue_token,
    revoke_token,
    resolve_token,
    list_tokens,
    purge_expired_tokens,
)


@click.group("token")
def token_cmd():
    """Manage access tokens for vault variables."""


@token_cmd.command("issue")
@click.argument("vault_name")
@click.argument("label")
@click.argument("keys", nargs=-1, required=True)
@click.option("--password", prompt=True, hide_input=True)
@click.option("--ttl", default=3600, show_default=True, help="TTL in seconds")
def token_issue(vault_name, label, keys, password, ttl):
    """Issue a token granting access to specific keys."""
    if not vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' does not exist", err=True)
        raise SystemExit(1)
    data = load_vault(vault_name, password)
    try:
        token = issue_token(data, label, list(keys), ttl_seconds=ttl)
        save_vault(vault_name, password, data)
        click.echo(f"Token issued: {token}")
    except TokenError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@token_cmd.command("revoke")
@click.argument("vault_name")
@click.argument("token")
@click.option("--password", prompt=True, hide_input=True)
def token_revoke(vault_name, token, password):
    """Revoke an access token."""
    if not vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' does not exist", err=True)
        raise SystemExit(1)
    data = load_vault(vault_name, password)
    try:
        revoke_token(data, token)
        save_vault(vault_name, password, data)
        click.echo("Token revoked.")
    except TokenError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@token_cmd.command("resolve")
@click.argument("vault_name")
@click.argument("token")
@click.option("--password", prompt=True, hide_input=True)
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]))
def token_resolve(vault_name, token, password, fmt):
    """Resolve a token to its allowed key/value pairs."""
    if not vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' does not exist", err=True)
        raise SystemExit(1)
    data = load_vault(vault_name, password)
    try:
        result = resolve_token(data, token)
        if fmt == "json":
            click.echo(json.dumps(result, indent=2))
        else:
            for k, v in result.items():
                click.echo(f"{k}={v}")
    except TokenError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@token_cmd.command("list")
@click.argument("vault_name")
@click.option("--password", prompt=True, hide_input=True)
def token_list(vault_name, password):
    """List all tokens and their metadata."""
    if not vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' does not exist", err=True)
        raise SystemExit(1)
    data = load_vault(vault_name, password)
    tokens = list_tokens(data)
    if not tokens:
        click.echo("No tokens found.")
        return
    for t in tokens:
        status = "EXPIRED" if t["expired"] else "active"
        click.echo(f"{t['token']}  [{status}]  label={t['label']}  keys={','.join(t['allowed_keys'])}")


@token_cmd.command("purge")
@click.argument("vault_name")
@click.option("--password", prompt=True, hide_input=True)
def token_purge(vault_name, password):
    """Remove all expired tokens from a vault."""
    if not vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' does not exist", err=True)
        raise SystemExit(1)
    data = load_vault(vault_name, password)
    count = purge_expired_tokens(data)
    save_vault(vault_name, password, data)
    click.echo(f"Purged {count} expired token(s).")
