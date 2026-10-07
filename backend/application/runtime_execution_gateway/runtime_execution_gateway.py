from __future__ import annotations

from backend.application.context.application_context_factory import (
    ApplicationContextFactory,
)
from backend.application.operational.runtime_execution_session.runtime_execution_session_flow_contract import (
    RuntimeExecutionSessionFlowContract,
)
from backend.application.runtime_execution_gateway.runtime_execution_gateway_contract import (
    ApplicationRuntimeExecutionGatewayContract,
)
from backend.application.runtime_execution_gateway.runtime_execution_session_flow_resolver import (
    RuntimeExecutionSessionFlowResolver,
)
from backend.core.agent.agent_request import AgentRequest
from backend.core.result import ExecutionResult
from backend.application.runtime_execution_gateway.runtime_execution_result_port import (
    ApplicationExecutionResultFactoryProtocol,
)


class ApplicationRuntimeExecutionGateway(
    ApplicationRuntimeExecutionGatewayContract,
):
    """
    Canonical application-to-runtime execution gateway.

    Owns:
        - request admission
        - request-scoped Context creation
        - runtime-session execution delegation
        - canonical result normalization

    Does not own:
        - Agent
        - RuntimeExecutionFlow
        - ProjectSession lifecycle
        - transport
        - startup lifecycle
    """

    VERSION = "1.2"

    def __init__(
        self,
        *,
        context_factory: ApplicationContextFactory,
        flow_resolver: RuntimeExecutionSessionFlowResolver,
        result_factory: ApplicationExecutionResultFactoryProtocol,
    ) -> None:
        if not isinstance(
            context_factory,
            ApplicationContextFactory,
        ):
            raise TypeError(
                "context_factory must ApplicationContextFactory"
            )

        if not isinstance(
            flow_resolver,
            RuntimeExecutionSessionFlowResolver,
        ):
            raise TypeError(
                "flow_resolver must "
                "RuntimeExecutionSessionFlowResolver"
            )

        if not isinstance(
            result_factory,
            ApplicationExecutionResultFactoryProtocol,
        ):
            raise TypeError(
                "result_factory must implement "
                "ApplicationExecutionResultFactoryProtocol"
            )

        factory = result_factory

        if not factory.ready():
            raise RuntimeError(
                "runtime result factory not ready"
            )

        self.context_factory = context_factory
        self.flow_resolver = flow_resolver
        self.result_factory = factory
        self.execution_count = 0
        self.failure_count = 0

    async def execute(
        self,
        *,
        request: AgentRequest,
        session_id: str,
        stream_callback: object | None = None,
    ) -> ExecutionResult:
        self._validate_request(
            request,
            session_id,
        )

        flow = self.flow_resolver.resolve()

        context = self.context_factory.create(
            request=request,
            session_id=session_id,
        )

        try:
            outputs = await flow.execute(
                request=request,
                context=context,
                stream_callback=stream_callback,
            )

            result = self.result_factory.create(
                outputs=outputs,
                request=request,
            )

            if not isinstance(
                result,
                ExecutionResult,
            ):
                raise TypeError(
                    "runtime result factory must return "
                    "ExecutionResult"
                )

            if not result.ready():
                raise RuntimeError(
                    "runtime execution result not ready"
                )

            self.execution_count += 1
            return result

        except Exception:
            self.failure_count += 1
            raise

    def ready(self) -> bool:
        return (
            self.context_factory.ready()
            and self.flow_resolver.ready()
            and self.result_factory.ready()
        )

    def execution_ready(self) -> bool:
        return (
            self.ready()
            and self.flow_resolver.bound()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "execution_ready": self.execution_ready(),
            "execution_count": self.execution_count,
            "failure_count": self.failure_count,
            "context_factory": (
                self.context_factory.dump()
            ),
            "flow_resolver": (
                self.flow_resolver.dump()
            ),
            "result_factory": (
                self.result_factory.dump()
            ),
        }

    @staticmethod
    def _validate_request(
        request: AgentRequest,
        session_id: str,
    ) -> None:
        if not isinstance(
            request,
            AgentRequest,
        ):
            raise TypeError(
                "request must AgentRequest"
            )

        if not request.ready():
            raise ValueError(
                "request not ready"
            )

        if not isinstance(
            session_id,
            str,
        ) or not session_id.strip():
            raise ValueError(
                "session id required"
            )

        if request.session_id.strip() != session_id.strip():
            raise ValueError(
                "request/session_id mismatch"
            )


__all__ = [
    "ApplicationRuntimeExecutionGateway",
]
