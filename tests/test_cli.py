import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from env_vault.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_init_creates_vault(runner):
    with patch("env_vault.cli.vault_exists", return_value=False), \
         patch("env_vault.cli.save_vault") as mock_save:
        result = runner.invoke(cli, ["init", "myproject"], input="secret\nsecret\n")
        assert result.exit_code == 0
        assert "created" in result.output
        mock_save.assert_called_once_with("myproject", {}, "secret")


def test_init_fails_if_vault_exists(runner):
    with patch("env_vault.cli.vault_exists", return_value=True):
        result = runner.invoke(cli, ["init", "myproject"], input="secret\nsecret\n")
        assert result.exit_code == 1
        assert "already exists" in result.output


def test_set_variable(runner):
    with patch("env_vault.cli.vault_exists", return_value=True), \
         patch("env_vault.cli.load_vault", return_value={}) as mock_load, \
         patch("env_vault.cli.save_vault") as mock_save:
        result = runner.invoke(cli, ["set", "myproject", "DB_URL", "postgres://localhost"], input="secret\n")
        assert result.exit_code == 0
        assert "Set 'DB_URL'" in result.output
        mock_save.assert_called_once_with("myproject", {"DB_URL": "postgres://localhost"}, "secret")


def test_set_fails_if_vault_missing(runner):
    with patch("env_vault.cli.vault_exists", return_value=False):
        result = runner.invoke(cli, ["set", "ghost", "KEY", "val"], input="secret\n")
        assert result.exit_code == 1
        assert "does not exist" in result.output


def test_get_variable(runner):
    with patch("env_vault.cli.vault_exists", return_value=True), \
         patch("env_vault.cli.load_vault", return_value={"API_KEY": "abc123"}):
        result = runner.invoke(cli, ["get", "myproject", "API_KEY"], input="secret\n")
        assert result.exit_code == 0
        assert "abc123" in result.output


def test_get_missing_key(runner):
    with patch("env_vault.cli.vault_exists", return_value=True), \
         patch("env_vault.cli.load_vault", return_value={}):
        result = runner.invoke(cli, ["get", "myproject", "MISSING"], input="secret\n")
        assert result.exit_code == 1
        assert "not found" in result.output


def test_list_vars(runner):
    with patch("env_vault.cli.vault_exists", return_value=True), \
         patch("env_vault.cli.load_vault", return_value={"FOO": "bar", "BAZ": "qux"}):
        result = runner.invoke(cli, ["list", "myproject"], input="secret\n")
        assert result.exit_code == 0
        assert "FOO=bar" in result.output
        assert "BAZ=qux" in result.output


def test_list_empty_vault(runner):
    with patch("env_vault.cli.vault_exists", return_value=True), \
         patch("env_vault.cli.load_vault", return_value={}):
        result = runner.invoke(cli, ["list", "myproject"], input="secret\n")
        assert result.exit_code == 0
        assert "empty" in result.output


def test_vaults_command(runner):
    with patch("env_vault.cli.list_vaults", return_value=["proj1", "proj2"]):
        result = runner.invoke(cli, ["vaults"])
        assert result.exit_code == 0
        assert "proj1" in result.output
        assert "proj2" in result.output


def test_vaults_command_empty(runner):
    with patch("env_vault.cli.list_vaults", return_value=[]):
        result = runner.invoke(cli, ["vaults"])
        assert result.exit_code == 0
        assert "No vaults found" in result.output
