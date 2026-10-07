"""Mixin 3 of JobRunner."""
from __future__ import annotations
from backend.core.observability.silent import swallow

from .part1 import (JobEvent, OnEvent, asyncio,)  # noqa: F401
class _Mixin3:
    @staticmethod
    async def _emit(on_event: OnEvent | None, event: JobEvent) -> None:
        if on_event is None:
            return
        try:
            result = on_event(event)
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            swallow("finetune.job._runner_parts.mixin3:16", e)
