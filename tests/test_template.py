"""Tests for env_vault.template."""

import pytest

from env_vault.template import render_template, collect_placeholders, TemplateError


# ---------------------------------------------------------------------------
# collect_placeholders
# ---------------------------------------------------------------------------

def test_collect_placeholders_basic():
    tmpl = "Hello {{ NAME }}, your token is {{ TOKEN }}."
    assert collect_placeholders(tmpl) == ["NAME", "TOKEN"]


def test_collect_placeholders_deduplicates():
    tmpl = "{{ KEY }} and {{ KEY }} again"
    assert collect_placeholders(tmpl) == ["KEY"]


def test_collect_placeholders_empty():
    assert collect_placeholders("no placeholders here") == []


def test_collect_placeholders_ignores_invalid_names():
    # Numbers-only or starting with digit are not matched
    tmpl = "{{ 123 }} {{ _VALID }} {{ also_valid }}"
    result = collect_placeholders(tmpl)
    assert "_VALID" in result
    assert "also_valid" in result
    assert "123" not in result


# ---------------------------------------------------------------------------
# render_template — happy path
# ---------------------------------------------------------------------------

def test_render_simple_substitution():
    result = render_template("Hello {{ NAME }}!", {"NAME": "World"})
    assert result == "Hello World!"


def test_render_multiple_placeholders():
    tmpl = "{{ A }} + {{ B }} = {{ C }}"
    result = render_template(tmpl, {"A": "1", "B": "2", "C": "3"})
    assert result == "1 + 2 = 3"


def test_render_extra_vars_ignored():
    result = render_template("{{ X }}", {"X": "ok", "Y": "ignored"})
    assert result == "ok"


def test_render_whitespace_inside_braces():
    result = render_template("{{  KEY  }}", {"KEY": "value"})
    assert result == "value"


# ---------------------------------------------------------------------------
# render_template — strict mode
# ---------------------------------------------------------------------------

def test_render_strict_raises_on_missing_key():
    with pytest.raises(TemplateError, match="undefined variable"):
        render_template("{{ MISSING }}", {}, strict=True)


def test_render_strict_reports_all_missing_keys():
    tmpl = "{{ A }} {{ B }} {{ C }}"
    with pytest.raises(TemplateError) as exc_info:
        render_template(tmpl, {}, strict=True)
    msg = str(exc_info.value)
    assert "A" in msg
    assert "B" in msg
    assert "C" in msg


# ---------------------------------------------------------------------------
# render_template — non-strict mode
# ---------------------------------------------------------------------------

def test_render_non_strict_leaves_placeholder():
    result = render_template("{{ MISSING }}", {}, strict=False)
    assert "{{ MISSING }}" in result


def test_render_non_strict_partial_substitution():
    result = render_template("{{ A }} {{ B }}", {"A": "hello"}, strict=False)
    assert result == "hello {{ B }}"
