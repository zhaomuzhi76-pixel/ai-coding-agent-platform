from __future__ import annotations

from backend.api.submission_api_router_factory import (
    SubmissionAPIRouterFactory,
)
from backend.api.submission_e2e_contract import (
    APISubmissionE2EProtocol,
)
from backend.api.submission_route import (
    APISubmissionRoute,
)
from backend.application.runtime_execution_gateway import (
    ApplicationRuntimeExecutionGatewayContract,
)
from backend.core.agent.agent_request import AgentRequest
from backend.core.result import ExecutionResult


class APISubmissionE2E(
    APISubmissionE2EProtocol,
):
    """
    Canonical real FastAPI Submission E2E assembly.

    Owns only:
        - canonical execution-gateway binding
        - request normalization
        - submission route composition
        - submission router composition

    Does not own:
        - capability resolution
        - AgentService execution
        - execution construction
        - queue
        - scheduler
        - dispatch
        - retry
        - transport server lifecycle
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

        self.route = APISubmissionRoute(
            execution_gateway
        )

        self.router = (
            SubmissionAPIRouterFactory()
            .create(self.route)
        )

        if not self.route.ready():
            raise RuntimeError(
                "submission route unavailable"
            )

        if not self.router.ready():
            raise RuntimeError(
                "submission router unavailable"
            )

    async def execute(
        self,
        payload: dict[str, object],
    ) -> ExecutionResult:
        if not isinstance(
            payload,
            dict,
        ):
            raise TypeError(
                "submission payload must be dict"
            )

        session_id = payload.get(
            "session_id"
        )

        if not isinstance(
            session_id,
            str,
        ) or not session_id.strip():
            raise ValueError(
                "session id required"
            )

        request_payload = dict(
            payload
        )
        request_payload.pop(
            "session_id",
            None,
        )

        result = await self.route.execute(
            request_payload,
            session_id,
        )

        if not isinstance(
            result,
            ExecutionResult,
        ):
            raise TypeError(
                "submission E2E must return ExecutionResult"
            )

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
            and self.route.ready()
            and self.router.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "execution_gateway": type(
                self.execution_gateway
            ).__name__,
            "route": self.route.dump(),
            "router": self.router.dump(),
        }


__all__ = [
    "APISubmissionE2E",
]
