"""Tests for env_vault/pipeline.py"""

import pytest
from env_vault.pipeline import (
    PipelineError,
    PipelineStep,
    build_pipeline,
    run_pipeline,
    pipeline_summary,
)


def _upper_keys(data: dict) -> dict:
    return {k.upper(): v for k, v in data.items()}


def _add_prefix(data: dict) -> dict:
    return {f"APP_{k}": v for k, v in data.items()}


def _bad_step(data: dict) -> list:
    return []


def _raising_step(data: dict) -> dict:
    raise ValueError("boom")


def test_build_pipeline_returns_steps():
    steps = build_pipeline([("upper", _upper_keys)])
    assert len(steps) == 1
    assert isinstance(steps[0], PipelineStep)
    assert steps[0].name == "upper"


def test_build_pipeline_empty_raises():
    with pytest.raises(PipelineError, match="at least one step"):
        build_pipeline([])


def test_run_pipeline_single_step():
    data = {"foo": "bar"}
    steps = build_pipeline([("upper", _upper_keys)])
    result, log = run_pipeline(data, steps)
    assert result == {"FOO": "bar"}
    assert len(log) == 1
    assert log[0]["step"] == "upper"
    assert log[0]["keys"] == 1


def test_run_pipeline_multiple_steps():
    data = {"name": "alice"}
    steps = build_pipeline([("upper", _upper_keys), ("prefix", _add_prefix)])
    result, log = run_pipeline(data, steps)
    assert "APP_NAME" in result
    assert len(log) == 2


def test_run_pipeline_no_steps_raises():
    with pytest.raises(PipelineError, match="No steps"):
        run_pipeline({}, [])


def test_run_pipeline_step_returns_non_dict_raises():
    steps = build_pipeline([("bad", _bad_step)])
    with pytest.raises(PipelineError, match="must return a dict"):
        run_pipeline({"x": "1"}, steps)


def test_run_pipeline_step_exception_wrapped():
    steps = build_pipeline([("raiser", _raising_step)])
    with pytest.raises(PipelineError, match="Step 'raiser' failed"):
        run_pipeline({"x": "1"}, steps)


def test_run_pipeline_preserves_original_data():
    original = {"KEY": "value"}
    steps = build_pipeline([("prefix", _add_prefix)])
    result, _ = run_pipeline(original, steps)
    assert "KEY" in original  # original not mutated
    assert "APP_KEY" in result


def test_pipeline_summary_format():
    log = [{"step": "upper", "keys": 3}, {"step": "prefix", "keys": 3}]
    summary = pipeline_summary(log)
    assert "upper" in summary
    assert "prefix" in summary
    assert "3 keys" in summary


def test_pipeline_summary_empty_log():
    summary = pipeline_summary([])
    assert "Pipeline run:" in summary


def test_pipeline_step_repr():
    step = PipelineStep("my_step", _upper_keys)
    assert "my_step" in repr(step)
