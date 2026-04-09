"""Integration tests for the export / import CLI commands."""

import json
import os
import pytest
from click.testing import CliRunner

from env_vault.cli import cli
from env_vault.storage import _vault_path


@pytest.fixture()
def runner(tmp_path, monkeypatch):
    monkeypatch.setenv("ENV_VAULT_DIR", str(tmp_path))
    return CliRunner()


@pytest.fixture()
def seeded_vault(runner):
    """Create a vault with two variables pre-loaded."""
    runner.invoke(cli, ["init", "myapp"], input="secret\nsecret\n")
    runner.invoke(cli, ["set", "myapp", "DB_HOST", "localhost"], input="secret\n")
    runner.invoke(cli, ["set", "myapp", "DB_PORT", "5432"], input="secret\n")
    return runner


def test_export_dotenv_stdout(seeded_vault):
    result = seeded_vault.invoke(cli, ["export", "myapp", "--format", "dotenv"], input="secret\n")
    assert result.exit_code == 0
    assert "DB_HOST=localhost" in result.output
    assert "DB_PORT=5432" in result.output


def test_export_json_stdout(seeded_vault):
    result = seeded_vault.invoke(cli, ["export", "myapp", "--format", "json"], input="secret\n")
    assert result.exit_code == 0
    data = json.loads(result.output.strip())
    assert data["DB_HOST"] == "localhost"


def test_export_to_file(seeded_vault, tmp_path):
    out_file = str(tmp_path / "vars.env")
    result = seeded_vault.invoke(
        cli, ["export", "myapp", "--output", out_file], input="secret\n"
    )
    assert result.exit_code == 0
    assert os.path.exists(out_file)
    content = open(out_file).read()
    assert "DB_HOST" in content


def test_export_wrong_password(seeded_vault):
    result = seeded_vault.invoke(cli, ["export", "myapp"], input="wrong\n")
    assert result.exit_code != 0


def test_export_missing_vault(runner):
    result = runner.invoke(cli, ["export", "ghost"], input="secret\n")
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_import_dotenv_file(seeded_vault, tmp_path):
    env_file = tmp_path / "extra.env"
    env_file.write_text("NEW_KEY=new_value\n")
    result = seeded_vault.invoke(
        cli, ["import", "myapp", str(env_file)], input="secret\n"
    )
    assert result.exit_code == 0
    assert "1 variable" in result.output


def test_import_conflict_without_overwrite(seeded_vault, tmp_path):
    env_file = tmp_path / "conflict.env"
    env_file.write_text("DB_HOST=newhost\n")
    result = seeded_vault.invoke(
        cli, ["import", "myapp", str(env_file)], input="secret\n"
    )
    assert result.exit_code != 0
    assert "Conflicting" in result.output


def test_import_conflict_with_overwrite(seeded_vault, tmp_path):
    env_file = tmp_path / "conflict.env"
    env_file.write_text("DB_HOST=newhost\n")
    result = seeded_vault.invoke(
        cli, ["import", "myapp", str(env_file), "--overwrite"], input="secret\n"
    )
    assert result.exit_code == 0
