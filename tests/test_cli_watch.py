"""Tests for env_vault.cli_watch."""

from __future__ import annotations

import threading
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from env_vault.cli_watch import watch_cmd
from env_vault.watch import WatchError


@pytest.fixture
def runner():
    return CliRunner()


import pytest


@pytest.fixture
def runner():
    return CliRunner()


def _invoke(runner, args, input_text=None):
    return runner.invoke(watch_cmd, args, input=input_text, catch_exceptions=False)


def test_watch_start_missing_vault(runner):
    with patch("env_vault.cli_watch.watch_vault") as mock_watch:
        mock_watch.side_effect = WatchError("Vault 'x' does not exist.")
        result = runner.invoke(
            watch_cmd,
            ["start", "x", "--password", "pw"],
            catch_exceptions=False,
        )
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_watch_start_prints_header(runner):
    stop = threading.Event()

    def fake_watch(vault_name, password, callback, interval, stop_event, load_fn=None):
        stop_event.set()  # stop immediately

    with patch("env_vault.cli_watch.watch_vault", side_effect=fake_watch):
        result = runner.invoke(
            watch_cmd,
            ["start", "myvault", "--password", "secret", "--interval", "1"],
            catch_exceptions=False,
        )

    assert "Watching 'myvault'" in result.output
    assert "1.0s" in result.output


def test_watch_callback_prints_added(runner):
    """Simulate the callback being invoked with an added key."""
    from env_vault.watch import WatchEvent

    captured_callback = {}

    def fake_watch(vault_name, password, callback, interval, stop_event, load_fn=None):
        captured_callback["fn"] = callback
        stop_event.set()

    with patch("env_vault.cli_watch.watch_vault", side_effect=fake_watch):
        runner.invoke(
            watch_cmd,
            ["start", "v", "--password", "pw"],
            catch_exceptions=False,
        )

    # Now manually fire the callback to verify output formatting
    from io import StringIO
    import click

    output = StringIO()
    event = WatchEvent(vault_name="v", added={"NEW_KEY": "hello"})
    with patch("click.echo", side_effect=lambda msg: output.write(str(msg) + "\n")):
        captured_callback["fn"](event)

    assert "[+] NEW_KEY=hello" in output.getvalue()


def test_watch_callback_prints_removed(runner):
    from env_vault.watch import WatchEvent
    from io import StringIO

    captured_callback = {}

    def fake_watch(vault_name, password, callback, interval, stop_event, load_fn=None):
        captured_callback["fn"] = callback
        stop_event.set()

    with patch("env_vault.cli_watch.watch_vault", side_effect=fake_watch):
        runner.invoke(watch_cmd, ["start", "v", "--password", "pw"], catch_exceptions=False)

    output = StringIO()
    event = WatchEvent(vault_name="v", removed=["OLD_KEY"])
    with patch("click.echo", side_effect=lambda msg: output.write(str(msg) + "\n")):
        captured_callback["fn"](event)

    assert "[-] OLD_KEY" in output.getvalue()


def test_watch_callback_prints_changed(runner):
    from env_vault.watch import WatchEvent
    from io import StringIO

    captured_callback = {}

    def fake_watch(vault_name, password, callback, interval, stop_event, load_fn=None):
        captured_callback["fn"] = callback
        stop_event.set()

    with patch("env_vault.cli_watch.watch_vault", side_effect=fake_watch):
        runner.invoke(watch_cmd, ["start", "v", "--password", "pw"], catch_exceptions=False)

    output = StringIO()
    event = WatchEvent(vault_name="v", changed={"KEY": "new_val"})
    with patch("click.echo", side_effect=lambda msg: output.write(str(msg) + "\n")):
        captured_callback["fn"](event)

    assert "[~] KEY=new_val" in output.getvalue()
