"""Template rendering for env-vault: substitute vault variables into template strings."""

import re
from typing import Dict, Optional


class TemplateError(Exception):
    """Raised when template rendering fails."""


_PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


def render_template(
    template: str,
    variables: Dict[str, str],
    *,
    strict: bool = True,
) -> str:
    """Replace ``{{ KEY }}`` placeholders in *template* with values from *variables*.

    Parameters
    ----------
    template:
        Raw template string containing ``{{ KEY }}`` placeholders.
    variables:
        Mapping of variable names to their values (typically loaded from a vault).
    strict:
        When *True* (default) a :class:`TemplateError` is raised for any
        placeholder whose key is not present in *variables*.  When *False*
        unresolved placeholders are left as-is.
    """
    missing = []

    def _replace(match: re.Match) -> str:
        key = match.group(1)
        if key in variables:
            return variables[key]
        if strict:
            missing.append(key)
            return match.group(0)  # keep original while collecting all missing
        return match.group(0)

    result = _PLACEHOLDER_RE.sub(_replace, template)

    if missing:
        keys = ", ".join(sorted(set(missing)))
        raise TemplateError(f"Template references undefined variable(s): {keys}")

    return result


def collect_placeholders(template: str) -> list:
    """Return a sorted list of unique placeholder names found in *template*."""
    return sorted({m.group(1) for m in _PLACEHOLDER_RE.finditer(template)})
