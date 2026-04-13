"""CLI commands for managing key subscriptions."""
import json as _json
import click

from env_vault.subscription import (
    SubscriptionError,
    subscribe,
    unsubscribe,
    list_subscriptions,
    list_all_subscriptions,
)
from env_vault.storage import load_vault, save_vault, vault_exists


def _load(name):
    return load_vault(name)


def _save(name, data):
    save_vault(name, data)


@click.group("subscription")
def subscription_cmd():
    """Manage key subscriptions."""


@subscription_cmd.command("add")
@click.argument("vault")
@click.argument("key")
@click.argument("subscriber")
@click.option("--channel", default="default", show_default=True)
@click.option("--tag", "tags", multiple=True, help="Optional tags")
def sub_add(vault, key, subscriber, channel, tags):
    """Subscribe SUBSCRIBER to KEY in VAULT."""
    if not vault_exists(vault):
        click.echo(f"Error: vault '{vault}' does not exist.", err=True)
        raise SystemExit(1)
    try:
        entry = subscribe(vault, key, subscriber, channel, list(tags), load_fn=_load, save_fn=_save)
        click.echo(f"Subscribed '{entry.subscriber}' to '{entry.key}' on channel '{entry.channel}'.")
    except SubscriptionError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@subscription_cmd.command("remove")
@click.argument("vault")
@click.argument("key")
@click.argument("subscriber")
@click.option("--channel", default="default", show_default=True)
def sub_remove(vault, key, subscriber, channel):
    """Unsubscribe SUBSCRIBER from KEY in VAULT."""
    if not vault_exists(vault):
        click.echo(f"Error: vault '{vault}' does not exist.", err=True)
        raise SystemExit(1)
    removed = unsubscribe(vault, key, subscriber, channel, load_fn=_load, save_fn=_save)
    if removed:
        click.echo(f"Removed subscription of '{subscriber}' from '{key}' on channel '{channel}'.")
    else:
        click.echo(f"No matching subscription found.", err=True)
        raise SystemExit(1)


@subscription_cmd.command("list")
@click.argument("vault")
@click.argument("key", required=False)
@click.option("--json", "as_json", is_flag=True)
def sub_list(vault, key, as_json):
    """List subscriptions for KEY (or all keys) in VAULT."""
    if not vault_exists(vault):
        click.echo(f"Error: vault '{vault}' does not exist.", err=True)
        raise SystemExit(1)
    if key:
        entries = list_subscriptions(vault, key, load_fn=_load)
    else:
        mapping = list_all_subscriptions(vault, load_fn=_load)
        entries = [e for lst in mapping.values() for e in lst]
    if as_json:
        click.echo(_json.dumps([{"key": e.key, "subscriber": e.subscriber, "channel": e.channel, "tags": e.tags} for e in entries], indent=2))
    else:
        if not entries:
            click.echo("No subscriptions found.")
        for e in entries:
            click.echo(f"{e.key}  {e.subscriber}  [{e.channel}]")
