from __future__ import annotations

from backend.application.runtime_execution_gateway import (
    ApplicationRuntimeExecutionGatewayContract,
)
from backend.application.runtime_submission_contract import (
    ApplicationRuntimeSubmissionProtocol,
)
from backend.core.agent.agent_request import AgentRequest
from backend.core.result import ExecutionResult


class ApplicationRuntimeSubmission(
    ApplicationRuntimeSubmissionProtocol,
):
    """
    Canonical runtime submission boundary.

    Owns:
        - canonical execution-gateway binding
        - runtime submission execution delegation
        - execution metrics
        - readiness projection

    Does not own:
        - submission capability resolution
        - AgentService delegation
        - execution construction
        - queue
        - scheduler
        - retry
        - dispatch
        - transport
    """

    VERSION = "2.0"

    def __init__(
        self,
        execution_gateway: ApplicationRuntimeExecutionGatewayContract,
    ) -> None:
        if not isinstance(
            execution_gateway,
            ApplicationRuntimeExecutionGatewayContract,
        ):
            raise TypeError(
                "execution_gateway must implement "
                "ApplicationRuntimeExecutionGatewayContract"
            )

        if not execution_gateway.ready():
            raise RuntimeError(
                "runtime execution gateway not ready"
            )

        self.execution_gateway = execution_gateway
        self.execution_count = 0

    async def execute(
        self,
        request: AgentRequest,
        session_id: str,
    ) -> ExecutionResult:
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

        result = await self.execution_gateway.execute(
            request=request,
            session_id=session_id,
        )

        if not isinstance(
            result,
            ExecutionResult,
        ):
            raise TypeError(
                "runtime submission must return "
                "ExecutionResult"
            )

        self.execution_count += 1
        return result

    def ready(
        self,
    ) -> bool:
        return (
            isinstance(
                self.execution_gateway,
                ApplicationRuntimeExecutionGatewayContract,
            )
            and self.execution_gateway.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "execution_count": self.execution_count,
            "execution_gateway": type(
                self.execution_gateway
            ).__name__,
        }


__all__ = [
    "ApplicationRuntimeSubmission",
]
