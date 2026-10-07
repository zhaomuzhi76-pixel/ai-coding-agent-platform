from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.agent.agent_request import (
    AgentRequest,
)
from backend.core.contracts.value import (
    CoreValue,
)
from backend.core.result import (
    ExecutionResult,
)


@runtime_checkable
class ApplicationExecutionResultFactoryProtocol(
    Protocol,
):
    """
    Application-owned execution result creation port.

    Application depends only on this contract.
    Concrete result normalization remains outside
    the Application gateway implementation.
    """

    def create(
        self,
        *,
        outputs: list[CoreValue],
        request: AgentRequest,
    ) -> ExecutionResult:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        ...


__all__ = [
    "ApplicationExecutionResultFactoryProtocol",
]
