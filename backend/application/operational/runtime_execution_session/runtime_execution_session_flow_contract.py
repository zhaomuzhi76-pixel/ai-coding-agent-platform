from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from backend.core.execution.execution_flow_protocol import ExecutionFlowProtocol
from backend.application.operational.runtime_execution_session.runtime_execution_session_context_protocol import (
    RuntimeExecutionSessionContextProtocol,
)
from backend.core.agent.agent_request import (
    AgentRequest,
)
from backend.core.contracts.value import (
    CoreValue,
)


@runtime_checkable
class RuntimeExecutionSessionFlowContract(
    Protocol,
):
    """
    Application operational runtime-session execution contract.

    Owns:
        - active project-session admission
        - request/session consistency
        - delegation to runtime execution flow

    Does not own:
        - project-session lifecycle mutation
        - planning
        - graph construction
        - DAG execution
        - result construction
        - transport
        - persistence
    """

    async def execute(
        self,
        *,
        request: AgentRequest,
        context: RuntimeExecutionSessionContextProtocol,
        stream_callback: Callable[..., CoreValue] | None = None,
    ) -> list[CoreValue]:
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
    "RuntimeExecutionSessionFlowContract",
]
