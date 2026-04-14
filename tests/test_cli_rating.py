"""Tests for env_vault.cli_rating."""

from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from env_vault.cli_rating import rating_cmd
from env_vault.rating import RatingResult


@pytest.fixture()
def runner():
    return CliRunner()


_GOOD_RESULT = RatingResult(
    grade="A",
    score=95,
    findings=0,
    summary="Score 95/100 (raw 95, -0 for 0 lint issue(s))",
)


@pytest.fixture()
def patched():
    with (
        patch("env_vault.cli_rating.vault_exists", return_value=True) as ve,
        patch("env_vault.cli_rating.rate_vault", return_value=_GOOD_RESULT) as rv,
    ):
        yield ve, rv


def test_rating_show_text_output(runner, patched):
    result = runner.invoke(rating_cmd, ["show", "myvault", "--password", "secret"])
    assert result.exit_code == 0
    assert "A" in result.output
    assert "95" in result.output


def test_rating_show_json_output(runner, patched):
    result = runner.invoke(
        rating_cmd,
        ["show", "myvault", "--password", "secret", "--format", "json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["grade"] == "A"
    assert data["score"] == 95
    assert data["vault"] == "myvault"


def test_rating_show_missing_vault(runner):
    with patch("env_vault.cli_rating.vault_exists", return_value=False):
        result = runner.invoke(rating_cmd, ["show", "nope", "--password", "x"])
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_rating_show_rating_error(runner):
    from env_vault.rating import RatingError

    with (
        patch("env_vault.cli_rating.vault_exists", return_value=True),
        patch("env_vault.cli_rating.rate_vault", side_effect=RatingError("bad pw")),
    ):
        result = runner.invoke(rating_cmd, ["show", "myvault", "--password", "wrong"])
    assert result.exit_code != 0
    assert "bad pw" in result.output
