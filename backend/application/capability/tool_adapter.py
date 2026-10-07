from __future__ import annotations

from typing import Any

from backend.application.capability.tool_contract import (
    ToolApplicationCapabilityProtocol,
)
from backend.application.tool.service import (
    ToolApplicationService,
)
from backend.core.tools.execution_contract import (
    ToolExecutionRequest,
    ToolExecutionResult,
)


class ToolApplicationCapabilityAdapter(
    ToolApplicationCapabilityProtocol,
):
    """
    Application capability adapter for canonical tool execution.

    Owns only application capability lifecycle and delegation.
    """

    VERSION = "1.0"
    NAME = "tools.execution"

    def __init__(
        self,
        service: ToolApplicationService,
    ) -> None:
        if not isinstance(
            service,
            ToolApplicationService,
        ):
            raise TypeError(
                "service must ToolApplicationService"
            )

        self.service = service
        self.initialized = False
        self.shutdown_count = 0
        self.execution_count = 0

    @property
    def name(self) -> str:
        return self.NAME

    @property
    def version(self) -> str:
        return self.VERSION

    def capabilities(self) -> tuple[str, ...]:
        return (
            "tool.execute",
        )

    async def execute(
        self,
        request: ToolExecutionRequest,
    ) -> ToolExecutionResult:
        if not self.initialized:
            raise RuntimeError(
                "tool application capability not enabled"
            )

        result = await self.service.execute(
            request
        )

        if not isinstance(
            result,
            ToolExecutionResult,
        ):
            raise TypeError(
                "tool application service must return "
                "ToolExecutionResult"
            )

        if not result.ready():
            raise RuntimeError(
                "tool execution result not ready"
            )

        self.execution_count += 1
        return result

    def initialize(
        self,
        context: Any = None,
    ) -> None:
        if not self.service.ready():
            raise RuntimeError(
                "tool application service not ready"
            )

        self.initialized = True

    def shutdown(self) -> None:
        self.initialized = False
        self.shutdown_count += 1

    def ready(self) -> bool:
        return self.service.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "capabilities": self.capabilities(),
            "initialized": self.initialized,
            "shutdown_count": self.shutdown_count,
            "execution_count": self.execution_count,
            "service": type(
                self.service
            ).__name__,
            "service_ready": self.service.ready(),
            "ready": self.ready(),
        }


__all__ = [
    "ToolApplicationCapabilityAdapter",
]
