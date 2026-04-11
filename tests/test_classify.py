"""Tests for env_vault.classify."""

from __future__ import annotations

import pytest

from env_vault.classify import (
    ClassifyError,
    ClassifyResult,
    classify_key,
    classify_vars,
    summary,
)


# ---------------------------------------------------------------------------
# classify_key
# ---------------------------------------------------------------------------


def test_classify_key_secret():
    result = classify_key("DB_PASSWORD")
    assert result.category == "secret"
    assert result.confidence >= 0.85


def test_classify_key_token():
    result = classify_key("GITHUB_TOKEN")
    assert result.category == "secret"


def test_classify_key_api_key():
    result = classify_key("STRIPE_API_KEY")
    assert result.category == "secret"


def test_classify_key_url():
    result = classify_key("DATABASE_URL")
    assert result.category == "url"
    assert result.confidence >= 0.80


def test_classify_key_host():
    result = classify_key("REDIS_HOST")
    assert result.category == "url"


def test_classify_key_config_port():
    result = classify_key("APP_PORT")
    assert result.category == "config"
    assert result.confidence >= 0.75


def test_classify_key_config_debug():
    result = classify_key("DEBUG")
    assert result.category == "config"


def test_classify_key_unknown():
    result = classify_key("APP_NAME")
    assert result.category == "unknown"
    assert result.confidence == 0.50


def test_classify_key_returns_classify_result_instance():
    result = classify_key("SOME_KEY")
    assert isinstance(result, ClassifyResult)


def test_classify_key_empty_string_raises():
    with pytest.raises(ClassifyError):
        classify_key("")


def test_classify_key_non_string_raises():
    with pytest.raises(ClassifyError):
        classify_key(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# classify_vars
# ---------------------------------------------------------------------------


def test_classify_vars_returns_list():
    results = classify_vars({"DB_PASSWORD": "s3cr3t", "APP_PORT": "8080"})
    assert isinstance(results, list)
    assert len(results) == 2


def test_classify_vars_sorted_by_key():
    results = classify_vars({"Z_KEY": "1", "A_KEY": "2", "M_KEY": "3"})
    keys = [r.key for r in results]
    assert keys == sorted(keys)


def test_classify_vars_empty_dict():
    results = classify_vars({})
    assert results == []


def test_classify_vars_non_dict_raises():
    with pytest.raises(ClassifyError):
        classify_vars(["not", "a", "dict"])  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------


def test_summary_counts_categories():
    results = classify_vars({
        "DB_PASSWORD": "x",
        "GITHUB_TOKEN": "y",
        "DATABASE_URL": "z",
        "APP_PORT": "80",
        "APP_NAME": "myapp",
    })
    counts = summary(results)
    assert counts["secret"] == 2
    assert counts["url"] == 1
    assert counts["config"] == 1
    assert counts["unknown"] == 1


def test_summary_empty_results():
    assert summary([]) == {}
