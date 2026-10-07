from __future__ import annotations

from backend.application.operational.project_session.project_session_operational_contract import (
    ProjectSessionOperationalContract,
)
from backend.core.execution.execution_flow_protocol import ExecutionFlowProtocol
from backend.application.operational.runtime_execution_session.runtime_execution_session_flow import (
    RuntimeExecutionSessionFlow,
)
from backend.application.operational.runtime_execution_session.runtime_execution_session_flow_support import (
    RuntimeExecutionSessionFlowSupport,
)


class RuntimeExecutionSessionFlowFactory:
    """
    Constructor for runtime execution session flow.

    Owns:
        - dependency validation
        - new-layer assembly

    Does not own:
        - project-session creation
        - runtime flow construction
        - runtime execution
    """

    VERSION = "2.0"

    def create(
        self,
        *,
        operational: ProjectSessionOperationalContract,
        runtime_flow: ExecutionFlowProtocol,
        support: RuntimeExecutionSessionFlowSupport | None = None,
    ) -> RuntimeExecutionSessionFlow:
        if operational is None:
            raise ValueError(
                "project session operational required"
            )

        if runtime_flow is None:
            raise ValueError(
                "runtime execution flow required"
            )

        flow = RuntimeExecutionSessionFlow(
            operational=operational,
            runtime_flow=runtime_flow,
            support=support,
        )

        if not flow.ready():
            raise RuntimeError(
                "runtime execution session flow unavailable"
            )

        return flow

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
    "RuntimeExecutionSessionFlowFactory",
]
