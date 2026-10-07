from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.context.context_protocol import (
    ContextProtocol,
)


@runtime_checkable
class RuntimeExecutionSessionContextProtocol(
    ContextProtocol,
    Protocol,
):
    """
    Application-owned runtime-session context capability.

    Responsibility:
        - expose the authoritative ProjectSession identity
        - preserve the existing Core ContextProtocol boundary

    Not Responsible:
        - request identity
        - trace identity
        - lifecycle transition
        - runtime execution
        - persistence
    """

    @property
    def session_id(
        self,
    ) -> str:
        ...


__all__ = [
    "RuntimeExecutionSessionContextProtocol",
]
