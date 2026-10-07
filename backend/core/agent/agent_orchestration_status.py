from __future__ import annotations

from enum import StrEnum


class AgentOrchestrationStatus(StrEnum):
    """Canonical task-level orchestration outcome."""

    COMPLETED = "completed"
    CONTINUE = "continue"
    REPLAN = "replan"
    FAILED = "failed"


__all__ = [
    "AgentOrchestrationStatus",
]
