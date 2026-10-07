from __future__ import annotations

from backend.application.context.application_context_factory import (
    ApplicationContextFactory,
)
from backend.application.runtime_execution_gateway import (
    ApplicationRuntimeExecutionGatewayFactory,
    RuntimeExecutionSessionFlowResolver,
)
from backend.application.runtime_execution_gateway.runtime_execution_gateway_contract import (
    ApplicationRuntimeExecutionGatewayContract,
)
from backend.application.runtime_execution_gateway.runtime_execution_result_port import (
    ApplicationExecutionResultFactoryProtocol,
)


class ApplicationAgentExecutionAssembly:
    """
    Agent execution assembly boundary.

    Owns:
        - flow resolver construction
        - execution gateway construction

    Does not own:
        - agent kernel
        - agent service
        - runtime implementation
    """

    VERSION = "1.0"

    def create_flow_resolver(
        self,
    ) -> RuntimeExecutionSessionFlowResolver:

        resolver = RuntimeExecutionSessionFlowResolver()

        if not resolver.ready():
            raise RuntimeError(
                "execution flow resolver unavailable"
            )

        return resolver

    def create_gateway(
        self,
        *,
        flow_resolver: RuntimeExecutionSessionFlowResolver,
        context_factory: ApplicationContextFactory,
        result_factory: ApplicationExecutionResultFactoryProtocol,
    ) -> ApplicationRuntimeExecutionGatewayContract:

        gateway = (
            ApplicationRuntimeExecutionGatewayFactory()
            .create(
                flow_resolver=flow_resolver,
                context_factory=context_factory,
                result_factory=result_factory,
            )
        )

        if not gateway.ready():
            raise RuntimeError(
                "execution gateway unavailable"
            )

        return gateway

    def bind_flow(
        self,
        *,
        resolver: RuntimeExecutionSessionFlowResolver,
        flow: object,
    ) -> None:
        if flow is None:
            raise ValueError(
                "runtime execution session flow required"
            )

        resolver.bind(flow)

        if not resolver.bound():
            raise RuntimeError(
                "runtime execution session flow bind failed"
            )

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationAgentExecutionAssembly",
]
