from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from backend.core.contracts.value import (
    CoreValue,
)
from backend.core.tools.argument_contract import (
    ToolArgumentValue,
    ToolArguments,
)


@dataclass(frozen=True)
class ToolExecutionRequest:
    """
    Core-owned canonical tool execution request.
    """

    tool_name: str
    arguments: ToolArguments = field(
        default_factory=dict
    )
    role: str = "runtime"
    request_id: str | None = None
    action: str = "execute"
    resource: str | None = None
    trace_id: str | None = None
    session_id: str | None = None
    agent_id: str | None = None
    metadata: ToolArguments = field(
        default_factory=dict
    )

    def ready(self) -> bool:
        return (
            isinstance(self.tool_name, str)
            and bool(self.tool_name.strip())
            and isinstance(self.arguments, dict)
            and isinstance(self.role, str)
            and bool(self.role.strip())
            and isinstance(self.action, str)
            and bool(self.action.strip())
            and isinstance(self.metadata, dict)
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": type(self).__name__,
            "tool_name": self.tool_name,
            "arguments": dict(self.arguments),
            "role": self.role,
            "request_id": self.request_id,
            "action": self.action,
            "resource": self.resource,
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "metadata": dict(self.metadata),
            "ready": self.ready(),
        }


@dataclass(frozen=True)
class ToolExecutionResult:
    """
    Core-owned canonical tool execution result.
    """

    tool_name: str
    success: bool
    output: ToolArgumentValue = None
    error: str | None = None
    metadata: ToolArguments = field(
        default_factory=dict
    )

    def ready(self) -> bool:
        if (
            not isinstance(self.tool_name, str)
            or not self.tool_name.strip()
            or not isinstance(self.success, bool)
            or not isinstance(self.metadata, dict)
        ):
            return False

        return (
            self.error is None
            if self.success
            else bool(self.error)
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": type(self).__name__,
            "tool_name": self.tool_name,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "metadata": dict(self.metadata),
            "ready": self.ready(),
        }


@runtime_checkable
class ToolCapabilityProtocol(Protocol):
    async def execute(
        self,
        request: ToolExecutionRequest,
    ) -> ToolExecutionResult:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        ...


__all__ = [
    "ToolCapabilityProtocol",
    "ToolExecutionRequest",
    "ToolExecutionResult",
]
