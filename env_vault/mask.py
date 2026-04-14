"""Masking module: partially reveal or fully hide variable values."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


class MaskError(Exception):
    """Raised when masking operations fail."""


@dataclass
class MaskResult:
    key: str
    original: str
    masked: str
    fully_hidden: bool

    def __repr__(self) -> str:
        return f"MaskResult(key={self.key!r}, masked={self.masked!r})"


def mask_value(
    value: str,
    *,
    reveal_chars: int = 4,
    mask_char: str = "*",
    fully_hidden: bool = False,
) -> str:
    """Return a masked version of *value*.

    Args:
        value: The plaintext value to mask.
        reveal_chars: Number of trailing characters to leave visible.
            Ignored when *fully_hidden* is True.
        mask_char: Character used for the hidden portion.
        fully_hidden: When True the entire value is replaced with mask chars.

    Returns:
        Masked string.
    """
    if not isinstance(value, str):
        raise MaskError("value must be a string")
    if len(mask_char) != 1:
        raise MaskError("mask_char must be a single character")
    if reveal_chars < 0:
        raise MaskError("reveal_chars must be >= 0")

    if fully_hidden or len(value) == 0:
        return mask_char * max(len(value), 8)

    if reveal_chars >= len(value):
        reveal_chars = 0

    hidden_len = len(value) - reveal_chars
    return mask_char * hidden_len + value[hidden_len:]


def mask_vars(
    variables: Dict[str, str],
    *,
    keys: Optional[list] = None,
    reveal_chars: int = 4,
    mask_char: str = "*",
    fully_hidden: bool = False,
) -> Dict[str, MaskResult]:
    """Mask a dictionary of environment variables.

    Args:
        variables: Mapping of key -> plaintext value.
        keys: Optional list of keys to mask; if None all keys are masked.
        reveal_chars: Passed through to :func:`mask_value`.
        mask_char: Passed through to :func:`mask_value`.
        fully_hidden: Passed through to :func:`mask_value`.

    Returns:
        Dict mapping each key to a :class:`MaskResult`.
    """
    target_keys = set(keys) if keys is not None else set(variables.keys())
    unknown = target_keys - set(variables.keys())
    if unknown:
        raise MaskError(f"Keys not found in vault: {sorted(unknown)}")

    results: Dict[str, MaskResult] = {}
    for key in target_keys:
        original = variables[key]
        masked = mask_value(
            original,
            reveal_chars=reveal_chars,
            mask_char=mask_char,
            fully_hidden=fully_hidden,
        )
        results[key] = MaskResult(
            key=key,
            original=original,
            masked=masked,
            fully_hidden=fully_hidden,
        )
    return results
