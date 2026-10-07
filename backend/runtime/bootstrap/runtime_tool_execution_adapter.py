from __future__ import annotations

from backend.core.tools.execution_contract import (
    ToolCapabilityProtocol,
    ToolExecutionRequest,
    ToolExecutionResult,
)
from backend.runtime.bootstrap.tool_runtime_provider import (
    RuntimeToolRuntimeProvider,
)


class RuntimeToolExecutionAdapter(
    ToolCapabilityProtocol,
):
    """
    Workspace-scoped ToolRuntime -> Core ToolCapability boundary.

    Responsibility:
        - resolve canonical ToolRuntime by workspace scope
        - delegate canonical tool execution
        - normalize runtime result into Core contract

    Not Responsible:
        - workspace construction
        - ToolRuntime construction
        - tool construction
        - scheduling
        - governance implementation
    """

    VERSION = "4.0"
    WORKSPACE_KEY = "workspace_root"

    def __init__(
        self,
        runtime_provider: RuntimeToolRuntimeProvider,
    ) -> None:
        if not isinstance(
            runtime_provider,
            RuntimeToolRuntimeProvider,
        ):
            raise TypeError(
                "runtime provider must "
                "RuntimeToolRuntimeProvider"
            )

        self.runtime_provider = runtime_provider

    async def execute(
        self,
        request: ToolExecutionRequest,
    ) -> ToolExecutionResult:
        self._validate_request(request)

        workspace_root = request.metadata.get(
            self.WORKSPACE_KEY
        )

        if (
            not isinstance(workspace_root, str)
            or not workspace_root.strip()
        ):
            raise ValueError(
                "workspace_root required for tool execution"
            )

        runtime = self.runtime_provider.create(
            workspace=workspace_root
        )

        if not runtime.ready():
            raise RuntimeError(
                "workspace tool runtime not ready"
            )

        result = await runtime.execute(
            request.tool_name,
            request.arguments,
            role=request.role,
            request_id=request.request_id,
            action=request.action,
            resource=request.resource,
            trace_id=request.trace_id,
            session_id=request.session_id,
            agent_id=request.agent_id,
        )

        return self._normalize_result(result)

    def ready(self) -> bool:
        return self.runtime_provider.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "workspace_key": self.WORKSPACE_KEY,
            "runtime_provider": type(
                self.runtime_provider
            ).__name__,
        }

    @staticmethod
    def _validate_request(
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

    @staticmethod
    def _normalize_result(
        result,
    ) -> ToolExecutionResult:
        canonical = ToolExecutionResult(
            tool_name=result.tool_name,
            success=bool(result.success),
            output=result.output,
            error=result.error,
            metadata={},
        )

        if not canonical.ready():
            raise RuntimeError(
                "adapted tool execution result not ready"
            )

        return canonical


__all__ = [
    "RuntimeToolExecutionAdapter",
]
