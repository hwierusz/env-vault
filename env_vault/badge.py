"""Badge generation for vault health/status summary."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


class BadgeError(Exception):
    """Raised when badge generation fails."""


# Thresholds for colour bands
_GREEN_MIN = 80
_YELLOW_MIN = 50


@dataclass
class Badge:
    label: str
    message: str
    color: str  # "green" | "yellow" | "red" | "blue"

    def __repr__(self) -> str:  # pragma: no cover
        return f"Badge(label={self.label!r}, message={self.message!r}, color={self.color!r})"

    def to_dict(self) -> Dict[str, str]:
        return {"label": self.label, "message": self.message, "color": self.color}

    def to_shields_url(self) -> str:
        """Return a shields.io static badge URL."""
        label = self.label.replace(" ", "_").replace("-", "--")
        message = self.message.replace(" ", "_").replace("-", "--")
        return f"https://img.shields.io/badge/{label}-{message}-{self.color}"


def _score_color(score: int) -> str:
    if score >= _GREEN_MIN:
        return "green"
    if score >= _YELLOW_MIN:
        return "yellow"
    return "red"


def generate_badges(vars: Dict[str, str], score: int) -> List[Badge]:
    """Generate a list of status badges for a vault.

    Args:
        vars:  The plain-text variable mapping (key -> value).
        score: Integer health score 0-100 (e.g. from score.py).

    Returns:
        List of Badge objects.
    """
    if not isinstance(score, int) or not (0 <= score <= 100):
        raise BadgeError(f"score must be an integer between 0 and 100, got {score!r}")

    badges: List[Badge] = []

    # 1. Health score badge
    badges.append(Badge(
        label="vault health",
        message=f"{score}%",
        color=_score_color(score),
    ))

    # 2. Variable count badge
    count = len(vars)
    badges.append(Badge(
        label="variables",
        message=str(count),
        color="blue",
    ))

    # 3. Empty-value warning badge
    empty = sum(1 for v in vars.values() if v == "")
    if empty:
        badges.append(Badge(
            label="empty values",
            message=str(empty),
            color="yellow" if empty < 3 else "red",
        ))
    else:
        badges.append(Badge(label="empty values", message="none", color="green"))

    return badges
