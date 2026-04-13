"""Workflow support: define and run ordered sequences of vault operations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


class WorkflowError(Exception):
    """Raised when a workflow step fails."""


@dataclass
class WorkflowStep:
    name: str
    fn: Callable[[Dict[str, str]], Dict[str, str]]
    description: str = ""

    def __repr__(self) -> str:  # pragma: no cover
        return f"WorkflowStep(name={self.name!r})"


@dataclass
class WorkflowResult:
    steps_run: List[str] = field(default_factory=list)
    vars_before: Dict[str, str] = field(default_factory=dict)
    vars_after: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"WorkflowResult(steps={self.steps_run}, "
            f"success={self.success})"
        )


def build_workflow(step_names: List[str], registry: Dict[str, WorkflowStep]) -> List[WorkflowStep]:
    """Resolve step names to WorkflowStep objects from the registry."""
    steps: List[WorkflowStep] = []
    for name in step_names:
        if name not in registry:
            raise WorkflowError(f"Unknown workflow step: {name!r}")
        steps.append(registry[name])
    return steps


def run_workflow(
    vars_: Dict[str, str],
    steps: List[WorkflowStep],
    stop_on_error: bool = True,
) -> WorkflowResult:
    """Execute a list of WorkflowSteps against *vars_*, returning a WorkflowResult."""
    result = WorkflowResult(vars_before=dict(vars_))
    current = dict(vars_)
    for step in steps:
        try:
            current = step.fn(current)
            result.steps_run.append(step.name)
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"{step.name}: {exc}")
            if stop_on_error:
                break
    result.vars_after = current
    return result


# ---------------------------------------------------------------------------
# Built-in steps
# ---------------------------------------------------------------------------

def _strip_empty(vars_: Dict[str, str]) -> Dict[str, str]:
    return {k: v for k, v in vars_.items() if v.strip() != ""}


def _uppercase_keys(vars_: Dict[str, str]) -> Dict[str, str]:
    return {k.upper(): v for k, v in vars_.items()}


def _strip_whitespace_values(vars_: Dict[str, str]) -> Dict[str, str]:
    return {k: v.strip() for k, v in vars_.items()}


DEFAULT_REGISTRY: Dict[str, WorkflowStep] = {
    "strip_empty": WorkflowStep("strip_empty", _strip_empty, "Remove keys with empty values"),
    "uppercase_keys": WorkflowStep("uppercase_keys", _uppercase_keys, "Uppercase all key names"),
    "strip_whitespace": WorkflowStep("strip_whitespace", _strip_whitespace_values, "Strip whitespace from values"),
}
