from __future__ import annotations

from backend.application.operational.project_session.project_session_operational_contract import (
    ProjectSessionOperationalContract,
)
from backend.application.operational.runtime_execution_session.runtime_execution_session_context_protocol import (
    RuntimeExecutionSessionContextProtocol,
)
from backend.core.agent.agent_request import AgentRequest


class RuntimeExecutionSessionFlowSupport:
    """
    Validation support for runtime execution session flow.

    Owns:
        - dependency validation
        - request validation
        - runtime-session context validation
        - authoritative session identity resolution

    Does not own:
        - session lifecycle
        - context storage
        - runtime execution
        - identity generation
    """

    VERSION = "3.0"

    def validate_operational(
        self,
        operational: object,
    ) -> ProjectSessionOperationalContract:
        if not isinstance(
            operational,
            ProjectSessionOperationalContract,
        ):
            raise TypeError(
                "operational must implement "
                "ProjectSessionOperationalContract"
            )

        if not operational.ready():
            raise RuntimeError(
                "project session operational not ready"
            )

        return operational

    @staticmethod
    def validate_runtime_flow(
        flow: object,
    ) -> object:
        if flow is None:
            raise ValueError(
                "runtime execution flow required"
            )

        execute = getattr(
            flow,
            "execute",
            None,
        )
        ready = getattr(
            flow,
            "ready",
            None,
        )

        if not callable(execute):
            raise TypeError(
                "runtime execution flow must expose execute()"
            )

        if not callable(ready):
            raise TypeError(
                "runtime execution flow must expose ready()"
            )

        if not ready():
            raise RuntimeError(
                "runtime execution flow not ready"
            )

        return flow

    @staticmethod
    def validate_request(
        request: AgentRequest,
    ) -> AgentRequest:
        if not isinstance(
            request,
            AgentRequest,
        ):
            raise TypeError(
                "request must be AgentRequest"
            )

        if not request.ready():
            raise ValueError(
                "AgentRequest not ready"
            )

        session_id = getattr(
            request,
            "session_id",
            None,
        )

        if not isinstance(
            session_id,
            str,
        ) or not session_id.strip():
            raise ValueError(
                "request session_id required"
            )

        return request

    @staticmethod
    def validate_context(
        context: RuntimeExecutionSessionContextProtocol,
    ) -> RuntimeExecutionSessionContextProtocol:
        if not isinstance(
            context,
            RuntimeExecutionSessionContextProtocol,
        ):
            raise TypeError(
                "context must implement "
                "RuntimeExecutionSessionContextProtocol"
            )

        if not context.ready():
            raise RuntimeError(
                "runtime session context not ready"
            )

        session_id = context.session_id

        if not isinstance(
            session_id,
            str,
        ) or not session_id.strip():
            raise ValueError(
                "context session_id required"
            )

        return context

    @classmethod
    def resolve_session_id(
        cls,
        request: AgentRequest,
        context: RuntimeExecutionSessionContextProtocol,
    ) -> str:
        request_session_id = request.session_id.strip()
        context_session_id = context.session_id.strip()

        if request_session_id != context_session_id:
            raise ValueError(
                "request/context session identity mismatch"
            )

        return context_session_id

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
    "RuntimeExecutionSessionFlowSupport",
]
