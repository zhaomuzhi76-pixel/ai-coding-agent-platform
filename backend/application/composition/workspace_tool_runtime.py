from __future__ import annotations

from typing import Any

from backend.application.composition.tool_runtime_port import (
    ApplicationToolRuntimeProtocol,
)
from backend.application.composition.runtime_port_adapter import (
    ApplicationRuntimePortAdapter,
)
from backend.core.tools.argument_contract import ToolArguments
from backend.core.tools.result_contract import ToolResultProtocol


class ApplicationWorkspaceToolRuntime(
    ApplicationToolRuntimeProtocol,
):
    """
    Application-owned workspace-scoped ToolRuntime facade.

    Owns only:
        - request workspace-scope selection
        - default startup workspace fallback
        - delegation to Runtime ToolRuntime

    Does not own:
        - ToolRuntime construction
        - builtin registration
        - tool discovery
        - filesystem access
        - tool execution policy
    """

    VERSION = "1.0"
    WORKSPACE_KEY = "workspace_root"

    def __init__(
        self,
        *,
        runtime: ApplicationRuntimePortAdapter,
        default_workspace: object,
    ) -> None:
        if not isinstance(
            runtime,
            ApplicationRuntimePortAdapter,
        ):
            raise TypeError(
                "runtime must ApplicationRuntimePortAdapter"
            )

        self._validate_workspace(default_workspace)

        self.runtime = runtime
        self.default_workspace = str(
            default_workspace
        )

    @property
    def name(self) -> str:
        return "tools.runtime.workspace"

    @property
    def version(self) -> str:
        return self.VERSION

    async def execute(
        self,
        name: str,
        arguments: ToolArguments,
        **kwargs: object,
    ) -> ToolResultProtocol:
        workspace = self._workspace(
            kwargs.get("metadata")
        )

        tool_runtime = self.runtime.create_tool_runtime(
            workspace
        )

        return await tool_runtime.execute(
            name,
            arguments,
            role=kwargs.get("role"),
            request_id=kwargs.get("request_id"),
            action=str(
                kwargs.get("action", "execute")
            ),
            resource=kwargs.get("resource"),
            trace_id=kwargs.get("trace_id"),
            session_id=kwargs.get("session_id"),
            agent_id=kwargs.get("agent_id"),
        )

    def ready(self) -> bool:
        return (
            self.runtime.ready()
            and bool(self.default_workspace.strip())
        )

    def snapshot(self) -> dict[str, int]:
        return {}

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "workspace_key": self.WORKSPACE_KEY,
            "default_workspace": self.default_workspace,
            "ready": self.ready(),
            "runtime": type(self.runtime).__name__,
        }

    def _workspace(
        self,
        metadata: object,
    ) -> str:
        if isinstance(metadata, dict):
            value = metadata.get(
                self.WORKSPACE_KEY
            )
            if value is not None:
                self._validate_workspace(value)
                return str(value)

        return self.default_workspace

    @staticmethod
    def _validate_workspace(
        value: object,
    ) -> None:
        if not isinstance(value, str):
            raise TypeError(
                "workspace_root must str"
            )

        if not value.strip():
            raise ValueError(
                "workspace_root required"
            )


__all__ = [
    "ApplicationWorkspaceToolRuntime",
]
