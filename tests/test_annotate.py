"""Tests for env_vault.annotate."""

from __future__ import annotations

import pytest

from env_vault.annotate import (
    AnnotateError,
    get_annotation,
    list_annotations,
    remove_annotation,
    set_annotation,
)

_SECTION = "__annotations__"


def _make_load(data: dict):
    def _load(vault_name):
        return data
    return _load


def _make_save(store: dict):
    def _save(vault_name, data):
        store.update(data)
    return _save


@pytest.fixture()
def base_data():
    return {"API_KEY": "secret", "HOST": "localhost"}


def test_set_annotation_stores_note(base_data):
    saved = {}
    set_annotation("v", "API_KEY", "Primary API key", _make_load(base_data), _make_save(saved))
    assert saved[_SECTION]["API_KEY"] == "Primary API key"


def test_set_annotation_strips_whitespace(base_data):
    saved = {}
    set_annotation("v", "API_KEY", "  trimmed  ", _make_load(base_data), _make_save(saved))
    assert saved[_SECTION]["API_KEY"] == "trimmed"


def test_set_annotation_missing_key_raises(base_data):
    with pytest.raises(AnnotateError, match="not found"):
        set_annotation("v", "MISSING", "note", _make_load(base_data), _make_save({}))


def test_set_annotation_empty_note_raises(base_data):
    with pytest.raises(AnnotateError, match="must not be empty"):
        set_annotation("v", "API_KEY", "   ", _make_load(base_data), _make_save({}))


def test_get_annotation_returns_note():
    data = {"KEY": "val", _SECTION: {"KEY": "my note"}}
    result = get_annotation("v", "KEY", _make_load(data))
    assert result == "my note"


def test_get_annotation_returns_none_when_absent():
    data = {"KEY": "val"}
    result = get_annotation("v", "KEY", _make_load(data))
    assert result is None


def test_remove_annotation_deletes_entry():
    data = {"KEY": "val", _SECTION: {"KEY": "note"}}
    saved = {}
    remove_annotation("v", "KEY", _make_load(data), _make_save(saved))
    assert "KEY" not in saved.get(_SECTION, {})


def test_remove_annotation_missing_raises():
    data = {"KEY": "val"}
    with pytest.raises(AnnotateError, match="No annotation"):
        remove_annotation("v", "KEY", _make_load(data), _make_save({}))


def test_list_annotations_returns_all():
    data = {"A": "1", "B": "2", _SECTION: {"A": "note-a", "B": "note-b"}}
    result = list_annotations("v", _make_load(data))
    assert result == {"A": "note-a", "B": "note-b"}


def test_list_annotations_empty_when_none():
    data = {"A": "1"}
    result = list_annotations("v", _make_load(data))
    assert result == {}
