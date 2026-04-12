"""Pipeline: chain multiple vault transformations in sequence."""

from typing import Callable, List, Tuple, Any


class PipelineError(Exception):
    pass


class PipelineStep:
    def __init__(self, name: str, fn: Callable[[dict], dict]):
        self.name = name
        self.fn = fn

    def __repr__(self):
        return f"PipelineStep(name={self.name!r})"


def build_pipeline(steps: List[Tuple[str, Callable[[dict], dict]]]) -> List[PipelineStep]:
    """Build an ordered list of PipelineStep objects from (name, fn) tuples."""
    if not steps:
        raise PipelineError("Pipeline must contain at least one step.")
    return [PipelineStep(name, fn) for name, fn in steps]


def run_pipeline(data: dict, steps: List[PipelineStep]) -> Tuple[dict, List[dict]]:
    """Execute each step in order, returning the final data and a log of each step's output.

    Args:
        data: Initial vault variable dict.
        steps: Ordered list of PipelineStep objects.

    Returns:
        Tuple of (final_data, step_log) where step_log is a list of
        {"step": name, "keys": count} dicts.
    """
    if not steps:
        raise PipelineError("No steps provided to run_pipeline.")

    log: List[dict] = []
    current = dict(data)

    for step in steps:
        try:
            current = step.fn(current)
        except Exception as exc:
            raise PipelineError(f"Step '{step.name}' failed: {exc}") from exc

        if not isinstance(current, dict):
            raise PipelineError(
                f"Step '{step.name}' must return a dict, got {type(current).__name__}."
            )

        log.append({"step": step.name, "keys": len(current)})

    return current, log


def pipeline_summary(log: List[dict]) -> str:
    """Return a human-readable summary of a pipeline run log."""
    lines = [f"  [{i + 1}] {entry['step']} -> {entry['keys']} keys" for i, entry in enumerate(log)]
    return "Pipeline run:\n" + "\n".join(lines)
