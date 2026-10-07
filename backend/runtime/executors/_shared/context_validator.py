"""Extract required string value from context + runtime_context."""
from __future__ import annotations

from typing import Any


def required_context_value(
    key: str,
    context: Any,
    fallback: Any | None = None,
) -> str:
    value: Any = None
    getter = getattr(context, "get", None)
    if callable(getter):
        value = getter(key)
    if value is None and fallback is not None:
        fb = getattr(fallback, "get", None)
        if callable(fb):
            value = fb(key, None)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"{key} required")
    return value.strip()
