from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.agent.agent_request import AgentRequest
from backend.core.result import ExecutionResult


@runtime_checkable
class RuntimeResultFactoryProtocol(
    Protocol,
):
    """
    Runtime result creation boundary.

    Owns:
        - runtime output normalization
        - canonical ExecutionResult creation

    Does not own:
        - execution
        - transport
        - persistence
    """

    def create(
        self,
        *,
        outputs: list[object],
        request: AgentRequest,
    ) -> ExecutionResult:
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
    "RuntimeResultFactoryProtocol",
]
