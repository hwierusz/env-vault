"""Schema validation for vault variables."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class SchemaError(Exception):
    """Raised when schema validation fails."""


@dataclass
class SchemaRule:
    key: str
    required: bool = False
    pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    allowed_values: List[str] = field(default_factory=list)

    def validate(self, value: Optional[str]) -> List[str]:
        """Return list of violation messages for *value*."""
        errors: List[str] = []
        if value is None:
            if self.required:
                errors.append(f"{self.key}: required but missing")
            return errors
        if self.pattern and not re.fullmatch(self.pattern, value):
            errors.append(f"{self.key}: value does not match pattern '{self.pattern}'")
        if self.min_length is not None and len(value) < self.min_length:
            errors.append(f"{self.key}: value too short (min {self.min_length})")
        if self.max_length is not None and len(value) > self.max_length:
            errors.append(f"{self.key}: value too long (max {self.max_length})")
        if self.allowed_values and value not in self.allowed_values:
            errors.append(f"{self.key}: value not in allowed set {self.allowed_values}")
        return errors


def validate_vars(
    variables: Dict[str, str],
    rules: List[SchemaRule],
) -> List[str]:
    """Validate *variables* against *rules*; return all violation messages."""
    violations: List[str] = []
    for rule in rules:
        value = variables.get(rule.key)
        violations.extend(rule.validate(value))
    return violations


def rules_from_dict(raw: List[Dict[str, Any]]) -> List[SchemaRule]:
    """Build a list of :class:`SchemaRule` from a plain-dict representation."""
    rules: List[SchemaRule] = []
    for entry in raw:
        if "key" not in entry:
            raise SchemaError("Each schema rule must have a 'key' field")
        rules.append(
            SchemaRule(
                key=entry["key"],
                required=bool(entry.get("required", False)),
                pattern=entry.get("pattern"),
                min_length=entry.get("min_length"),
                max_length=entry.get("max_length"),
                allowed_values=list(entry.get("allowed_values", [])),
            )
        )
    return rules
