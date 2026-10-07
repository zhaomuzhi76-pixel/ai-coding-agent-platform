from __future__ import annotations

from backend.application.composition.tool_runtime_port import (
    ApplicationToolRuntimeProtocol,
)
from backend.core.tools.execution_contract import (
    ToolExecutionRequest,
    ToolExecutionResult,
)


class ToolApplicationService:
    """
    Application-owned tool execution service.

    Consumes only the application-visible runtime tool protocol.
    Runtime construction, registration, discovery, and governance
    remain outside the application layer.
    """

    VERSION = "2.0"

    def __init__(
        self,
        capability: ApplicationToolRuntimeProtocol,
    ) -> None:
        if not isinstance(
            capability,
            ApplicationToolRuntimeProtocol,
        ):
            raise TypeError(
                "capability must implement "
                "ApplicationToolRuntimeProtocol"
            )

        if not capability.ready():
            raise RuntimeError(
                "application tool runtime not ready"
            )

        self.capability = capability
        self.execution_count = 0
        self.failure_count = 0

    async def execute(
        self,
        request: ToolExecutionRequest,
    ) -> ToolExecutionResult:
        self._validate(request)

        try:
            result = await self.capability.execute(
                request.tool_name,
                request.arguments,
                role=request.role,
                request_id=request.request_id,
                action=request.action,
                resource=request.resource,
                trace_id=request.trace_id,
                session_id=request.session_id,
                agent_id=request.agent_id,
                metadata=request.metadata,
            )

            normalized = ToolExecutionResult(
                tool_name=request.tool_name,
                success=bool(
                    getattr(
                        result,
                        "success",
                        False,
                    )
                ),
                output=getattr(
                    result,
                    "output",
                    None,
                ),
                error=getattr(
                    result,
                    "error",
                    None,
                ),
                metadata={
                    **dict(
                        getattr(
                            result,
                            "metadata",
                            {},
                        )
                        or {}
                    ),
                    "action": request.action,
                },
            )

            if not normalized.ready():
                raise RuntimeError(
                    "normalized tool execution result "
                    "not ready"
                )

            self.execution_count += 1

            if not normalized.success:
                self.failure_count += 1

            return normalized

        except Exception as error:
            self.execution_count += 1
            self.failure_count += 1

            return ToolExecutionResult(
                tool_name=request.tool_name,
                success=False,
                error=str(error),
                metadata={
                    "action": request.action,
                    "exception": type(error).__name__,
                },
            )

    def ready(self) -> bool:
        return self.capability.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "execution_count": self.execution_count,
            "failure_count": self.failure_count,
            "capability": type(
                self.capability
            ).__name__,
        }

    @staticmethod
    def _validate(
        request: ToolExecutionRequest,
    ) -> None:
        if not isinstance(
            request,
            ToolExecutionRequest,
        ):
            raise TypeError(
                "request must ToolExecutionRequest"
            )

        if not request.ready():
            raise ValueError(
                "tool execution request not ready"
            )


__all__ = [
    "ToolApplicationService",
]
