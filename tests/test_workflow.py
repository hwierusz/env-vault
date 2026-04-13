"""Tests for env_vault.workflow."""
from __future__ import annotations

import pytest

from env_vault.workflow import (
    DEFAULT_REGISTRY,
    WorkflowError,
    WorkflowStep,
    WorkflowResult,
    build_workflow,
    run_workflow,
)


# ---------------------------------------------------------------------------
# build_workflow
# ---------------------------------------------------------------------------

def test_build_workflow_returns_steps():
    steps = build_workflow(["strip_empty", "uppercase_keys"], DEFAULT_REGISTRY)
    assert len(steps) == 2
    assert all(isinstance(s, WorkflowStep) for s in steps)


def test_build_workflow_unknown_step_raises():
    with pytest.raises(WorkflowError, match="Unknown workflow step"):
        build_workflow(["nonexistent"], DEFAULT_REGISTRY)


def test_build_workflow_empty_list():
    assert build_workflow([], DEFAULT_REGISTRY) == []


# ---------------------------------------------------------------------------
# run_workflow
# ---------------------------------------------------------------------------

def test_run_workflow_strip_empty():
    vars_ = {"KEY": "value", "EMPTY": "", "BLANK": "   "}
    steps = build_workflow(["strip_empty"], DEFAULT_REGISTRY)
    result = run_workflow(vars_, steps)
    assert result.success
    assert "EMPTY" not in result.vars_after
    assert "BLANK" not in result.vars_after
    assert result.vars_after["KEY"] == "value"


def test_run_workflow_uppercase_keys():
    vars_ = {"db_host": "localhost", "api_key": "secret"}
    steps = build_workflow(["uppercase_keys"], DEFAULT_REGISTRY)
    result = run_workflow(vars_, steps)
    assert "DB_HOST" in result.vars_after
    assert "API_KEY" in result.vars_after


def test_run_workflow_strip_whitespace_values():
    vars_ = {"KEY": "  hello  ", "OTHER": "\tworld\n"}
    steps = build_workflow(["strip_whitespace"], DEFAULT_REGISTRY)
    result = run_workflow(vars_, steps)
    assert result.vars_after["KEY"] == "hello"
    assert result.vars_after["OTHER"] == "world"


def test_run_workflow_chained_steps():
    vars_ = {"db_host": "  localhost  ", "empty": ""}
    steps = build_workflow(["strip_whitespace", "strip_empty", "uppercase_keys"], DEFAULT_REGISTRY)
    result = run_workflow(vars_, steps)
    assert result.vars_after == {"DB_HOST": "localhost"}
    assert result.steps_run == ["strip_whitespace", "strip_empty", "uppercase_keys"]


def test_run_workflow_vars_before_unchanged():
    vars_ = {"key": "val"}
    steps = build_workflow(["uppercase_keys"], DEFAULT_REGISTRY)
    result = run_workflow(vars_, steps)
    assert result.vars_before == {"key": "val"}


def test_run_workflow_error_stops_by_default():
    def _bad(_vars):
        raise RuntimeError("boom")

    bad_step = WorkflowStep("bad", _bad)
    good_step = WorkflowStep("good", lambda v: v)
    result = run_workflow({"K": "V"}, [bad_step, good_step])
    assert not result.success
    assert "bad: boom" in result.errors
    assert "good" not in result.steps_run


def test_run_workflow_no_stop_continues():
    def _bad(_vars):
        raise RuntimeError("boom")

    bad_step = WorkflowStep("bad", _bad)
    good_step = WorkflowStep("good", lambda v: v)
    result = run_workflow({"K": "V"}, [bad_step, good_step], stop_on_error=False)
    assert not result.success
    assert "good" in result.steps_run


def test_workflow_result_success_true_when_no_errors():
    result = WorkflowResult(steps_run=["a"], vars_before={}, vars_after={})
    assert result.success is True


def test_workflow_result_success_false_when_errors():
    result = WorkflowResult(errors=["step: oops"])
    assert result.success is False
