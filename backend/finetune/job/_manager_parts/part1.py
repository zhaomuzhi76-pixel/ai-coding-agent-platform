"""Part 1 of manager.py."""
from __future__ import annotations

import asyncio

from typing import Any, Awaitable, Callable

from ..event import JobEvent

from ..record import JobRecord, create_job_record

from ..runner import JobRunner

from ..spec import JobSpec

from ..state import JobState, is_terminal

from .. import store as _store

OnEvent = Callable[[JobEvent], Awaitable[None] | None]
