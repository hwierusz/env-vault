"""CLI tests for webhook commands."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from env_vault.cli_webhook import webhook_cmd
from env_vault.webhook import WebhookEntry, WebhookError

URL = "https://example.com/hook"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def patched(monkeypatch):
    """Return a namespace for patching webhook functions."""
    return monkeypatch


# ---------------------------------------------------------------------------
# webhook add
# ---------------------------------------------------------------------------

def test_webhook_add_success(runner, patched):
    patched.setattr("env_vault.cli_webhook.add_webhook",
                    lambda *a, **kw: None)
    result = runner.invoke(webhook_cmd, ["add", "myapp", URL,
                                         "--password", "secret"])
    assert result.exit_code == 0
    assert "registered" in result.output


def test_webhook_add_with_events(runner, patched):
    captured: dict = {}

    def _add(vault, pw, url, events=None, **kw):
        captured["events"] = events

    patched.setattr("env_vault.cli_webhook.add_webhook", _add)
    runner.invoke(webhook_cmd, ["add", "myapp", URL,
                                "--password", "pw",
                                "-e", "set", "-e", "delete"])
    assert captured["events"] == ["set", "delete"]


def test_webhook_add_error(runner, patched):
    patched.setattr("env_vault.cli_webhook.add_webhook",
                    lambda *a, **kw: (_ for _ in ()).throw(
                        WebhookError("already registered")))
    result = runner.invoke(webhook_cmd, ["add", "myapp", URL,
                                         "--password", "pw"])
    assert result.exit_code != 0
    assert "already registered" in result.output


# ---------------------------------------------------------------------------
# webhook remove
# ---------------------------------------------------------------------------

def test_webhook_remove_success(runner, patched):
    patched.setattr("env_vault.cli_webhook.remove_webhook",
                    lambda *a, **kw: None)
    result = runner.invoke(webhook_cmd, ["remove", "myapp", URL,
                                         "--password", "pw"])
    assert result.exit_code == 0
    assert "removed" in result.output


# ---------------------------------------------------------------------------
# webhook list
# ---------------------------------------------------------------------------

def test_webhook_list_shows_entries(runner, patched):
    patched.setattr(
        "env_vault.cli_webhook.list_webhooks",
        lambda *a, **kw: [
            WebhookEntry(url=URL, events=["set"]),
        ],
    )
    result = runner.invoke(webhook_cmd, ["list", "myapp", "--password", "pw"])
    assert result.exit_code == 0
    assert URL in result.output
    assert "set" in result.output


def test_webhook_list_empty(runner, patched):
    patched.setattr("env_vault.cli_webhook.list_webhooks",
                    lambda *a, **kw: [])
    result = runner.invoke(webhook_cmd, ["list", "myapp", "--password", "pw"])
    assert "No webhooks" in result.output


# ---------------------------------------------------------------------------
# webhook fire
# ---------------------------------------------------------------------------

def test_webhook_fire_notified(runner, patched):
    patched.setattr("env_vault.cli_webhook.fire_event",
                    lambda *a, **kw: [URL])
    result = runner.invoke(webhook_cmd, ["fire", "myapp", "set",
                                         "--password", "pw"])
    assert result.exit_code == 0
    assert "1" in result.output


def test_webhook_fire_no_match(runner, patched):
    patched.setattr("env_vault.cli_webhook.fire_event",
                    lambda *a, **kw: [])
    result = runner.invoke(webhook_cmd, ["fire", "myapp", "set",
                                         "--password", "pw"])
    assert "No webhooks matched" in result.output
