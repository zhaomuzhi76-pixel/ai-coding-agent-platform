"""Mixin 1 of JobRunner."""
from __future__ import annotations
from .part1 import (Any,)  # noqa: F401
class _Mixin1:
    def __init__(self, backend_override: Any = None) -> None:
        self._backend_override = backend_override
