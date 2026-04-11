"""Tests for env_vault.expiry."""

from __future__ import annotations

import time
from typing import Dict

import pytest

from env_vault.expiry import ExpiryError, ExpiryReport, expiry_report, purge_expired


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NOW = time.time()


def _make_data(vars_: dict, ttls: dict | None = None) -> dict:
    data: dict = {"vars": vars_}
    if ttls:
        data["ttl"] = {k: NOW + v for k, v in ttls.items()}
    return data


def _loader(data: dict):
    def _load(name: str, password: str) -> dict:
        return data

    return _load


def _saver(store: list):
    def _save(name: str, password: str, data: dict) -> None:
        store.append(data)

    return _save


# ---------------------------------------------------------------------------
# ExpiryReport
# ---------------------------------------------------------------------------


def test_report_has_issues_false_when_all_healthy():
    r = ExpiryReport(vault_name="v", healthy=["A"])
    assert not r.has_issues


def test_report_has_issues_true_when_expired():
    r = ExpiryReport(vault_name="v", expired=["A"])
    assert r.has_issues


def test_report_has_issues_true_when_expiring_soon():
    r = ExpiryReport(vault_name="v", expiring_soon=["A"])
    assert r.has_issues


# ---------------------------------------------------------------------------
# expiry_report
# ---------------------------------------------------------------------------


def test_expiry_report_healthy_key():
    data = _make_data({"KEY": "val"}, ttls={"KEY": 9999})
    report = expiry_report("myv", _loader(data), "pw")
    assert "KEY" in report.healthy
    assert not report.expired
    assert not report.expiring_soon


def test_expiry_report_no_ttl_goes_to_healthy():
    data = _make_data({"KEY": "val"})
    report = expiry_report("myv", _loader(data), "pw")
    assert "KEY" in report.healthy


def test_expiry_report_expired_key():
    data = _make_data({"KEY": "val"})
    data["ttl"] = {"KEY": NOW - 1}  # already past
    report = expiry_report("myv", _loader(data), "pw")
    assert "KEY" in report.expired


def test_expiry_report_expiring_soon_key():
    data = _make_data({"KEY": "val"})
    data["ttl"] = {"KEY": NOW + 3600}  # 1 h — within default 24 h window
    report = expiry_report("myv", _loader(data), "pw")
    assert "KEY" in report.expiring_soon


def test_expiry_report_custom_warning_seconds():
    data = _make_data({"KEY": "val"})
    data["ttl"] = {"KEY": NOW + 3600}  # 1 h
    # warning window only 10 minutes — should be healthy
    report = expiry_report("myv", _loader(data), "pw", warning_seconds=600)
    assert "KEY" in report.healthy


def test_expiry_report_load_failure_raises():
    def bad_load(name, pw):
        raise RuntimeError("disk error")

    with pytest.raises(ExpiryError, match="disk error"):
        expiry_report("v", bad_load, "pw")


# ---------------------------------------------------------------------------
# purge_expired
# ---------------------------------------------------------------------------


def test_purge_expired_removes_expired_key():
    data = _make_data({"OLD": "v", "NEW": "v"}, ttls={"NEW": 9999})
    data["ttl"]["OLD"] = NOW - 1
    saved: list = []
    removed = purge_expired("v", _loader(data), _saver(saved), "pw")
    assert removed == ["OLD"]
    assert "OLD" not in saved[0]["vars"]
    assert "NEW" in saved[0]["vars"]


def test_purge_expired_no_expired_keys_does_not_save():
    data = _make_data({"KEY": "v"}, ttls={"KEY": 9999})
    saved: list = []
    removed = purge_expired("v", _loader(data), _saver(saved), "pw")
    assert removed == []
    assert saved == []


def test_purge_expired_load_failure_raises():
    def bad_load(name, pw):
        raise RuntimeError("boom")

    with pytest.raises(ExpiryError, match="boom"):
        purge_expired("v", bad_load, lambda *a: None, "pw")
