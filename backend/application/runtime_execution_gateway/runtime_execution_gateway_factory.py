from __future__ import annotations

from backend.application.context.application_context_factory import (
    ApplicationContextFactory,
)
from backend.application.runtime_execution_gateway.runtime_execution_gateway import (
    ApplicationRuntimeExecutionGateway,
)
from backend.application.runtime_execution_gateway.runtime_execution_result_port import (
    ApplicationExecutionResultFactoryProtocol,
)
from backend.application.runtime_execution_gateway.runtime_execution_session_flow_resolver import (
    RuntimeExecutionSessionFlowResolver,
)


class ApplicationRuntimeExecutionGatewayFactory:
    """
    Sole construction owner for ApplicationRuntimeExecutionGateway.

    Owns only:
        - dependency validation
        - gateway construction

    Does not own:
        - flow resolver creation
        - flow binding
        - runtime lifecycle
    """

    VERSION = "1.5"

    def create(
        self,
        *,
        flow_resolver: RuntimeExecutionSessionFlowResolver,
        context_factory: ApplicationContextFactory,
        result_factory: ApplicationExecutionResultFactoryProtocol,
    ) -> ApplicationRuntimeExecutionGateway:

        if not isinstance(
            flow_resolver,
            RuntimeExecutionSessionFlowResolver,
        ):
            raise TypeError(
                "flow_resolver must RuntimeExecutionSessionFlowResolver"
            )

        if not isinstance(
            context_factory,
            ApplicationContextFactory,
        ):
            raise TypeError(
                "context_factory must ApplicationContextFactory"
            )

        if not context_factory.ready():
            raise RuntimeError(
                "application context factory not ready"
            )

        if not isinstance(
            result_factory,
            ApplicationExecutionResultFactoryProtocol,
        ):
            raise TypeError(
                "result_factory must implement "
                "ApplicationExecutionResultFactoryProtocol"
            )

        if not result_factory.ready():
            raise RuntimeError(
                "application execution result factory not ready"
            )

        gateway = ApplicationRuntimeExecutionGateway(
            context_factory=context_factory,
            flow_resolver=flow_resolver,
            result_factory=result_factory,
        )

        if not gateway.ready():
            raise RuntimeError(
                "application runtime execution gateway unavailable"
            )

        return gateway

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
            "ownership": "gateway construction only",
        }


__all__ = [
    "ApplicationRuntimeExecutionGatewayFactory",
]
