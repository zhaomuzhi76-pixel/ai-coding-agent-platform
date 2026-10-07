from __future__ import annotations

from collections.abc import Callable

from backend.application.operational.project_session.project_session_operational_contract import (
    ProjectSessionOperationalContract,
)
from backend.core.execution.execution_flow_protocol import ExecutionFlowProtocol
from backend.application.operational.runtime_execution_session.runtime_execution_session_context_protocol import (
    RuntimeExecutionSessionContextProtocol,
)
from backend.application.operational.runtime_execution_session.runtime_execution_session_flow_contract import (
    RuntimeExecutionSessionFlowContract,
)
from backend.application.operational.runtime_execution_session.runtime_execution_session_flow_support import (
    RuntimeExecutionSessionFlowSupport,
)
from backend.core.agent.agent_request import (
    AgentRequest,
)
from backend.core.contracts.value import (
    CoreValue,
)


class RuntimeExecutionSessionFlow(
    RuntimeExecutionSessionFlowContract,
):
    """
    Session-gated application runtime execution flow.

    Owns:
        - request/context admission
        - session identity consistency
        - active project-session admission
        - runtime flow delegation

    Does not own:
        - session lifecycle mutation
        - planning
        - graph construction
        - DAG execution
        - result construction
    """

    VERSION = "3.1"

    def __init__(
        self,
        *,
        operational: ProjectSessionOperationalContract,
        runtime_flow: ExecutionFlowProtocol,
        support: RuntimeExecutionSessionFlowSupport | None = None,
    ) -> None:
        self.support = (
            support
            or RuntimeExecutionSessionFlowSupport()
        )

        self.operational = (
            self.support.validate_operational(
                operational
            )
        )

        flow = self.support.validate_runtime_flow(
            runtime_flow
        )

        if not isinstance(
            flow,
            ExecutionFlowProtocol,
        ):
            raise TypeError(
                "runtime flow must implement "
                "ExecutionFlowProtocol"
            )

        self.runtime_flow = flow
        self.execution_count = 0

    async def execute(
        self,
        *,
        request: AgentRequest,
        context: RuntimeExecutionSessionContextProtocol,
        stream_callback: Callable[..., CoreValue] | None = None,
    ) -> list[CoreValue]:
        request = self.support.validate_request(
            request
        )

        context = self.support.validate_context(
            context
        )

        session_id = (
            self.support.resolve_session_id(
                request,
                context,
            )
        )

        self.operational.require_active(
            session_id
        )

        outputs = await self.runtime_flow.execute(
            request=request,
            context=context,
            stream_callback=stream_callback,
        )

        if not isinstance(
            outputs,
            list,
        ):
            raise TypeError(
                "runtime execution flow must return list"
            )

        self.execution_count += 1

        return outputs

    def ready(
        self,
    ) -> bool:
        return (
            self.support.ready()
            and self.operational.ready()
            and self.runtime_flow.ready()
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "execution_count": self.execution_count,
            "ready": self.ready(),
            "operational": type(
                self.operational
            ).__name__,
            "runtime_flow": type(
                self.runtime_flow
            ).__name__,
            "support": self.support.dump(),
        }


__all__ = [
    "RuntimeExecutionSessionFlow",
]
