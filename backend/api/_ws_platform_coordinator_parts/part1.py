"""Part 1 of ws_platform_coordinator.py."""
from __future__ import annotations

import asyncio

from backend.workspace.path_normalizer import normalize_workspace_path

from typing import Any, Dict

from backend.core.result import ResultSerializer

from backend.api.ws_message_sender import WSMessageSender

from backend.application.agent_entry import dispatch

from backend.application.agent_runtime.multiplex.entry import (
    run_team_if_configured,
)

from backend.application.agent_loop.step_event import (
    to_runtime_event_v2,
)

from backend.workspace.workspace_path import normalize_only

__all__ = ["PlatformBackedCoordinator"]
