from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.protocols.dumpable import (
    DumpableProtocol,
)
from backend.core.protocols.ready import (
    ReadyProtocol,
)


@runtime_checkable
class ExecutionRequestProtocol(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Core-owned execution request boundary.

    Responsibility:
        - expose request readiness
        - expose request snapshot

    Not Responsible:
        - agent behavior
        - planning
        - runtime execution
        - transport
        - persistence
    """


__all__ = [
    "ExecutionRequestProtocol",
]
