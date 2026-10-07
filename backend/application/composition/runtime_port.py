from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.application.composition.agent_runtime_port import (
    ApplicationAgentRuntimePortProtocol,
)
from backend.application.composition.tool_runtime_port import (
    ApplicationToolRuntimeProtocol,
)
from backend.application.runtime_execution_gateway.runtime_execution_result_port import (
    ApplicationExecutionResultFactoryProtocol,
)
from backend.core.execution.execution_flow_protocol import (
    ExecutionFlowProtocol,
)


@runtime_checkable
class ApplicationRuntimePortProtocol(
    ApplicationAgentRuntimePortProtocol,
    Protocol,
):
    """
    Application-owned semantic boundary for Runtime.

    Application consumes semantic operations only.
    Runtime construction and generic capability discovery remain
    below this boundary.
    """

    def create_tool_runtime(
        self,
        workspace: object,
    ) -> ApplicationToolRuntimeProtocol:
        ...

    def create_result_factory(
        self,
    ) -> ApplicationExecutionResultFactoryProtocol:
        ...


    def create_execution_engine(
        self,
    ) -> object:
        ...


    def create_runtime_flow(
        self,
        *,
        preparer: object,
        executor: object,
    ) -> ExecutionFlowProtocol:
        ...

    def configure_executor(
        self,
        *,
        llm_provider: object,
        tools: object,
        modification: object,
    ) -> object:
        ...

    def infrastructure_ready(
        self,
    ) -> bool:
        ...

    def execution_ready(
        self,
    ) -> bool:
        ...

    def ready(
        self,
    ) -> bool:
        ...


__all__ = [
    "ApplicationRuntimePortProtocol",
]
