"""Tests for env_vault/cli_tags.py"""

import pytest
from click.testing import CliRunner
from env_vault.cli_tags import tag_cmd
from env_vault.tags import TAGS_META_KEY


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def patched(monkeypatch):
    store = {}

    def fake_load(name, password):
        return dict(store.get(name, {"VAR1": "val1", "VAR2": "val2"}))

    def fake_save(name, password, data):
        store[name] = dict(data)

    monkeypatch.setattr("env_vault.tags.load_vault", fake_load)
    monkeypatch.setattr("env_vault.tags.save_vault", fake_save)
    return store


def test_tag_add_success(runner, patched):
    result = runner.invoke(tag_cmd, ["add", "myvault", "VAR1", "production", "--password", "pass"])
    assert result.exit_code == 0
    assert "added" in result.output


def test_tag_add_missing_key_fails(runner, patched):
    result = runner.invoke(tag_cmd, ["add", "myvault", "MISSING", "tag1", "--password", "pass"])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_tag_remove_success(runner, patched, monkeypatch):
    # Pre-seed a tag
    from env_vault import tags as tags_mod
    tags_mod.add_tag("myvault", "pass", "VAR1", "staging")
    result = runner.invoke(tag_cmd, ["remove", "myvault", "VAR1", "staging", "--password", "pass"])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_tag_remove_missing_tag_fails(runner, patched):
    result = runner.invoke(tag_cmd, ["remove", "myvault", "VAR1", "ghost", "--password", "pass"])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_tag_list_shows_tags(runner, patched, monkeypatch):
    from env_vault import tags as tags_mod
    tags_mod.add_tag("myvault", "pass", "VAR1", "backend")
    result = runner.invoke(tag_cmd, ["list", "myvault", "--password", "pass"])
    assert result.exit_code == 0
    assert "VAR1" in result.output
    assert "backend" in result.output


def test_tag_list_empty(runner, patched):
    result = runner.invoke(tag_cmd, ["list", "myvault", "--password", "pass"])
    assert result.exit_code == 0
    assert "No tags" in result.output


def test_tag_find_returns_keys(runner, patched, monkeypatch):
    from env_vault import tags as tags_mod
    tags_mod.add_tag("myvault", "pass", "VAR1", "shared")
    tags_mod.add_tag("myvault", "pass", "VAR2", "shared")
    result = runner.invoke(tag_cmd, ["find", "myvault", "shared", "--password", "pass"])
    assert result.exit_code == 0
    assert "VAR1" in result.output
    assert "VAR2" in result.output


def test_tag_find_no_match(runner, patched):
    result = runner.invoke(tag_cmd, ["find", "myvault", "nope", "--password", "pass"])
    assert result.exit_code == 0
    assert "No variables" in result.output
