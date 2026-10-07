from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ExecutionFlowProtocol(Protocol):
    """
    Core-owned cross-layer execution flow capability.

    Owns:
        - canonical execution-flow invocation contract
        - readiness contract
        - diagnostic contract

    Does not own:
        - execution implementation
        - session admission
        - graph construction
        - node execution
        - result construction
    """

    async def execute(
        self,
        *,
        request,
        context,
        stream_callback=None,
    ) -> list[object]:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, object]:
        ...


__all__ = [
    "ExecutionFlowProtocol",
]
