"""CLI commands for webhook management."""

import click

from env_vault.webhook import (
    WebhookError,
    add_webhook,
    remove_webhook,
    list_webhooks,
    fire_event,
)


@click.group("webhook")
def webhook_cmd():
    """Manage webhook notifications for vault events."""


@webhook_cmd.command("add")
@click.argument("vault_name")
@click.argument("url")
@click.password_option("--password", "-p", prompt="Vault password")
@click.option(
    "--event",
    "-e",
    multiple=True,
    help="Event type to subscribe to (repeatable). Omit for all events.",
)
def webhook_add(vault_name: str, url: str, password: str, event: tuple):
    """Register a webhook URL for VAULT_NAME."""
    try:
        add_webhook(vault_name, password, url, list(event) if event else None)
        click.echo(f"Webhook '{url}' registered.")
    except WebhookError as exc:
        raise click.ClickException(str(exc))


@webhook_cmd.command("remove")
@click.argument("vault_name")
@click.argument("url")
@click.password_option("--password", "-p", prompt="Vault password")
def webhook_remove(vault_name: str, url: str, password: str):
    """Unregister a webhook URL from VAULT_NAME."""
    try:
        remove_webhook(vault_name, password, url)
        click.echo(f"Webhook '{url}' removed.")
    except WebhookError as exc:
        raise click.ClickException(str(exc))


@webhook_cmd.command("list")
@click.argument("vault_name")
@click.password_option("--password", "-p", prompt="Vault password")
def webhook_list(vault_name: str, password: str):
    """List all webhooks registered for VAULT_NAME."""
    try:
        hooks = list_webhooks(vault_name, password)
    except WebhookError as exc:
        raise click.ClickException(str(exc))

    if not hooks:
        click.echo("No webhooks registered.")
        return

    for h in hooks:
        events_str = ", ".join(h.events) if h.events else "all"
        click.echo(f"{h.url}  [{events_str}]")


@webhook_cmd.command("fire")
@click.argument("vault_name")
@click.argument("event")
@click.password_option("--password", "-p", prompt="Vault password")
def webhook_fire(vault_name: str, event: str, password: str):
    """Manually fire EVENT for VAULT_NAME webhooks."""
    try:
        notified = fire_event(vault_name, password, event)
    except WebhookError as exc:
        raise click.ClickException(str(exc))

    if not notified:
        click.echo("No webhooks matched.")
    else:
        click.echo(f"Notified {len(notified)} webhook(s).")
