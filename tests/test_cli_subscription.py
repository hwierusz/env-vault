"""Tests for env_vault.cli_subscription."""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from env_vault.cli_subscription import subscription_cmd
from env_vault.subscription import SubscriptionEntry, SubscriptionError


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def patched():
    with patch("env_vault.cli_subscription.vault_exists", return_value=True) as ve, \
         patch("env_vault.cli_subscription.subscribe") as sub, \
         patch("env_vault.cli_subscription.unsubscribe") as unsub, \
         patch("env_vault.cli_subscription.list_subscriptions") as ls, \
         patch("env_vault.cli_subscription.list_all_subscriptions") as la:
        yield {"vault_exists": ve, "subscribe": sub, "unsubscribe": unsub,
               "list_subscriptions": ls, "list_all_subscriptions": la}


def test_sub_add_success(runner, patched):
    patched["subscribe"].return_value = SubscriptionEntry(key="K", subscriber="alice", channel="default")
    result = runner.invoke(subscription_cmd, ["add", "myvault", "K", "alice"])
    assert result.exit_code == 0
    assert "alice" in result.output


def test_sub_add_missing_vault(runner, patched):
    patched["vault_exists"].return_value = False
    result = runner.invoke(subscription_cmd, ["add", "missing", "K", "alice"])
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_sub_add_subscription_error(runner, patched):
    patched["subscribe"].side_effect = SubscriptionError("already subscribed")
    result = runner.invoke(subscription_cmd, ["add", "myvault", "K", "alice"])
    assert result.exit_code != 0
    assert "already subscribed" in result.output


def test_sub_remove_success(runner, patched):
    patched["unsubscribe"].return_value = True
    result = runner.invoke(subscription_cmd, ["remove", "myvault", "K", "alice"])
    assert result.exit_code == 0
    assert "Removed" in result.output


def test_sub_remove_not_found(runner, patched):
    patched["unsubscribe"].return_value = False
    result = runner.invoke(subscription_cmd, ["remove", "myvault", "K", "alice"])
    assert result.exit_code != 0


def test_sub_list_for_key(runner, patched):
    patched["list_subscriptions"].return_value = [
        SubscriptionEntry(key="K", subscriber="alice", channel="default"),
    ]
    result = runner.invoke(subscription_cmd, ["list", "myvault", "K"])
    assert result.exit_code == 0
    assert "alice" in result.output


def test_sub_list_all_json(runner, patched):
    patched["list_all_subscriptions"].return_value = {
        "K": [SubscriptionEntry(key="K", subscriber="bob", channel="alerts")]
    }
    result = runner.invoke(subscription_cmd, ["list", "myvault", "--json"])
    assert result.exit_code == 0
    assert "bob" in result.output


def test_sub_list_empty(runner, patched):
    patched["list_all_subscriptions"].return_value = {}
    result = runner.invoke(subscription_cmd, ["list", "myvault"])
    assert result.exit_code == 0
    assert "No subscriptions" in result.output
