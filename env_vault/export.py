"""Export and import vault contents in various formats."""

import json
import os
from typing import Dict, Optional


SUPPORTED_FORMATS = ("json", "dotenv", "shell")


def export_vars(variables: Dict[str, str], fmt: str = "dotenv") -> str:
    """Serialize environment variables to the specified format."""
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}")

    if fmt == "json":
        return json.dumps(variables, indent=2)

    if fmt == "shell":
        lines = [f"export {k}={_shell_quote(v)}" for k, v in sorted(variables.items())]
        return "\n".join(lines)

    # dotenv (default)
    lines = [f"{k}={_dotenv_quote(v)}" for k, v in sorted(variables.items())]
    return "\n".join(lines)


def import_vars(content: str, fmt: str = "dotenv") -> Dict[str, str]:
    """Parse environment variables from the specified format string."""
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}")

    if fmt == "json":
        data = json.loads(content)
        if not isinstance(data, dict):
            raise ValueError("JSON content must be a top-level object")
        return {str(k): str(v) for k, v in data.items()}

    variables: Dict[str, str] = {}
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        # Strip leading 'export ' for shell format
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = _strip_quotes(value.strip())
        if key:
            variables[key] = value
    return variables


def _shell_quote(value: str) -> str:
    """Wrap value in single quotes, escaping internal single quotes."""
    return "'" + value.replace("'", "'\\''" ) + "'"


def _dotenv_quote(value: str) -> str:
    """Quote value with double quotes if it contains spaces or special chars."""
    if any(c in value for c in (" ", "\t", "\n", '"', "'", "#", "$", "`")):
        return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'
    return value


def _strip_quotes(value: str) -> str:
    """Remove surrounding quotes from a value string."""
    if len(value) >= 2:
        if (value[0] == '"' and value[-1] == '"') or (value[0] == "'" and value[-1] == "'"):
            return value[1:-1]
    return value
