"""CLI commands for vault expiry forecasting."""
import json
from datetime import timezone

import click

from env_vault.forecast import ForecastError, forecast_vault


@click.group("forecast")
def forecast_cmd() -> None:
    """Forecast TTL expiry events for vault variables."""


@forecast_cmd.command("show")
@click.argument("vault_name")
@click.password_option("--password", "-p", prompt="Vault password")
@click.option(
    "--warning",
    "-w",
    default=86400,
    show_default=True,
    help="Seconds before expiry to flag as warning.",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
)
@click.option(
    "--filter",
    "status_filter",
    type=click.Choice(["all", "ok", "warning", "expired"]),
    default="all",
    show_default=True,
    help="Show only entries with the given status.",
)
def forecast_show(
    vault_name: str,
    password: str,
    warning: int,
    fmt: str,
    status_filter: str,
) -> None:
    """Show expiry forecast for all TTL-enabled variables."""
    try:
        entries = forecast_vault(
            vault_name, password, warning_threshold=warning
        )
    except ForecastError as exc:
        raise click.ClickException(str(exc))

    if status_filter != "all":
        entries = [e for e in entries if e.status == status_filter]

    if not entries:
        click.echo("No TTL-enabled variables found.")
        return

    if fmt == "json":
        payload = [
            {
                "key": e.key,
                "expires_at": e.expires_at.astimezone(timezone.utc).isoformat(),
                "seconds_remaining": round(e.seconds_remaining, 2),
                "status": e.status,
            }
            for e in entries
        ]
        click.echo(json.dumps(payload, indent=2))
    else:
        status_symbols = {"ok": "✓", "warning": "!", "expired": "✗"}
        for e in entries:
            sym = status_symbols.get(e.status, "?")
            ts = e.expires_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            click.echo(f"[{sym}] {e.key:<30} expires {ts}  ({e.seconds_remaining:.0f}s)")
