"""Validate model identifier from provider context."""
from __future__ import annotations

from typing import Any


def required_model(context: Any, default: str = "") -> str:
    value: Any = None
    getter = getattr(context, "get", None)
    if callable(getter):
        value = getter("model")
    if value is None and default:
        value = default
    if not isinstance(value, str) or not value.strip():
        raise ValueError("model required")
    return value.strip()
