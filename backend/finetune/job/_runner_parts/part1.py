"""Part 1 of runner.py."""
from __future__ import annotations

import asyncio

import time

from dataclasses import dataclass

from typing import Any, Awaitable, Callable

from backend.finetune.config import FinetuneConfig

from backend.finetune.recipe import build_config

from ..event import (
    JobEvent,
    succeeded_event, failed_event, cancelled_event,
    started_event, log_event, progress_event,
)

from ..record import JobRecord

from ..state import JobState, validate_transition

OnEvent = Callable[[JobEvent], Awaitable[None] | None]

@dataclass
class RunHandle:
    """运行句柄（供取消/查询）。"""
    job_id: str
    task: asyncio.Task

__all__ = ["JobRunner", "RunHandle", "OnEvent"]
