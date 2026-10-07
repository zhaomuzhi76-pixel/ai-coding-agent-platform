from __future__ import annotations

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


class ApplicationRuntimePortAdapter(
    ApplicationAgentRuntimePortProtocol,
):
    """
    Application-to-Runtime semantic adapter.

    Application consumes semantic operations only.
    Generic capability discovery remains inside Runtime.
    """

    VERSION = "2.0"

    def __init__(self, runtime: object) -> None:
        if runtime is None:
            raise ValueError("runtime required")
        self.runtime = runtime

    def ready(self) -> bool:
        return bool(self.runtime.ready())

    def create_event_bus(self):
        return self.runtime.create_event_bus()

    def create_knowledge_middleware(self):
        return self.runtime.create_knowledge_middleware()

    def create_code_intelligence_capability(self):
        return self.runtime.create_code_intelligence_capability()

    def create_code_modification_provider(self):
        return self.runtime.create_code_modification_provider()

    def create_tool_runtime(
        self,
        workspace: object,
    ) -> ApplicationToolRuntimeProtocol:
        return self.runtime.create_tool_runtime(workspace)

    def create_result_factory(
        self,
    ) -> ApplicationExecutionResultFactoryProtocol:
        return self.runtime.create_result_factory()


    def create_execution_engine(self):
        return self.runtime.create_execution_engine()


    def create_runtime_flow(
        self,
        *,
        preparer: object,
        executor: object,
    ) -> ExecutionFlowProtocol:
        return self.runtime.create_runtime_flow(
            preparer=preparer,
            executor=executor,
        )

    def configure_executor(
        self,
        *,
        llm_provider: object,
        tools: object,
        modification: object,
    ):
        return self.runtime.configure_executor(
            llm_provider=llm_provider,
            tools=tools,
            modification=modification,
        )

    def infrastructure_ready(self) -> bool:
        return self.runtime.infrastructure_ready()

    def execution_ready(self) -> bool:
        return self.runtime.execution_ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "runtime": type(self.runtime).__name__,
        }


__all__ = [
    "ApplicationRuntimePortAdapter",
]
