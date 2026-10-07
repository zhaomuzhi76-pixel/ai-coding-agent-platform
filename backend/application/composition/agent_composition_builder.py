from __future__ import annotations

from backend.application.context.application_context_factory import (
    ApplicationContextFactory,
)
from backend.application.composition.agent_composition_builder_contract import (
    ApplicationAgentCompositionBuilderProtocol,
)
from backend.application.composition.agent_composition_builder_support import (
    ApplicationAgentCompositionBuilderSupport,
)
from backend.application.composition.agent_execution_assembly import (
    ApplicationAgentExecutionAssembly,
)
from backend.application.composition.agent_service_assembly import (
    ApplicationAgentServiceAssembly,
)
from backend.application.composition.agent_runtime_port import (
    ApplicationAgentRuntimePortProtocol,
)
class ApplicationAgentCompositionBuilder(
    ApplicationAgentCompositionBuilderProtocol,
):
    VERSION = "8.0"

    def __init__(
        self,
        support: (
            ApplicationAgentCompositionBuilderSupport | None
        ) = None,
    ) -> None:
        self.support = (
            support
            or ApplicationAgentCompositionBuilderSupport()
        )
        self.execution = ApplicationAgentExecutionAssembly()
        self.service = ApplicationAgentServiceAssembly()

    def create(
        self,
        *,

        runtime: ApplicationAgentRuntimePortProtocol,
        runtime_execution_session_flow: object,
        context_factory: ApplicationContextFactory,
    ) -> dict[str, object]:
        self.support.validate_inputs(

            runtime=runtime,
        )

        flow_resolver = self.execution.create_flow_resolver()

        self.execution.bind_flow(
            resolver=flow_resolver,
            flow=runtime_execution_session_flow,
        )

        result_factory = runtime.create_result_factory()

        if not result_factory.ready():
            raise RuntimeError("result factory unavailable")

        execution_gateway = self.execution.create_gateway(
            flow_resolver=flow_resolver,
            context_factory=context_factory,
            result_factory=result_factory,
        )

        agent_service = self.service.create(
            execution_gateway=execution_gateway,
        )

        return {
            "agent_service": agent_service,
            "runtime_execution_gateway": execution_gateway,
            "runtime_execution_session_flow_resolver": flow_resolver,
        }

    def ready(self) -> bool:
        return (
            self.support.ready()
            and self.execution.ready()
            and self.service.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "assemblies": ("execution", "service"),
        }


__all__ = ["ApplicationAgentCompositionBuilder"]
