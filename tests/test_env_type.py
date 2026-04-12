"""Tests for env_vault/env_type.py"""
import pytest

from env_vault.env_type import (
    EnvTypeError,
    coerce_value,
    get_type,
    list_typed_keys,
    remove_type,
    set_type,
)


def _base_data():
    return {
        "vars": {
            "PORT": "8080",
            "DEBUG": "true",
            "RATIO": "0.75",
            "CONFIG": '{"a": 1}',
            "NAME": "myapp",
        }
    }


def test_set_type_stores_type():
    data = _base_data()
    set_type(data, "PORT", "integer")
    assert data["__env_types__"]["PORT"] == "integer"


def test_set_type_missing_key_raises():
    data = _base_data()
    with pytest.raises(EnvTypeError, match="does not exist"):
        set_type(data, "MISSING", "string")


def test_set_type_invalid_type_raises():
    data = _base_data()
    with pytest.raises(EnvTypeError, match="Unknown type"):
        set_type(data, "PORT", "bytes")


def test_get_type_returns_declared_type():
    data = _base_data()
    set_type(data, "NAME", "string")
    assert get_type(data, "NAME") == "string"


def test_get_type_returns_none_when_unset():
    data = _base_data()
    assert get_type(data, "PORT") is None


def test_remove_type_deletes_entry():
    data = _base_data()
    set_type(data, "PORT", "integer")
    remove_type(data, "PORT")
    assert get_type(data, "PORT") is None


def test_remove_type_missing_raises():
    data = _base_data()
    with pytest.raises(EnvTypeError, match="No type declared"):
        remove_type(data, "PORT")


def test_coerce_integer():
    data = _base_data()
    set_type(data, "PORT", "integer")
    assert coerce_value(data, "PORT") == 8080


def test_coerce_boolean_true():
    data = _base_data()
    set_type(data, "DEBUG", "boolean")
    assert coerce_value(data, "DEBUG") is True


def test_coerce_float():
    data = _base_data()
    set_type(data, "RATIO", "float")
    assert coerce_value(data, "RATIO") == pytest.approx(0.75)


def test_coerce_json():
    data = _base_data()
    set_type(data, "CONFIG", "json")
    assert coerce_value(data, "CONFIG") == {"a": 1}


def test_coerce_no_type_raises():
    data = _base_data()
    with pytest.raises(EnvTypeError, match="No type declared"):
        coerce_value(data, "PORT")


def test_coerce_bad_value_raises():
    data = _base_data()
    data["vars"]["PORT"] = "not_a_number"
    set_type(data, "PORT", "integer")
    with pytest.raises(EnvTypeError, match="Cannot coerce"):
        coerce_value(data, "PORT")


def test_list_typed_keys_returns_all():
    data = _base_data()
    set_type(data, "PORT", "integer")
    set_type(data, "NAME", "string")
    result = list_typed_keys(data)
    assert result == {"PORT": "integer", "NAME": "string"}


def test_list_typed_keys_empty_when_none_set():
    data = _base_data()
    assert list_typed_keys(data) == {}
