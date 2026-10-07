from __future__ import annotations

from backend.core.tools.execution_contract import (
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolCapabilityProtocol,
)


class ToolExecutionPort:
    """
    Runtime-facing tool execution boundary.

    Core owns the canonical tool contract.
    Runtime owns only execution integration.
    """

    VERSION = "2.0"

    def __init__(
        self,
        capability: ToolCapabilityProtocol,
    ) -> None:
        if capability is None:
            raise ValueError(
                "tool capability required"
            )

        if not isinstance(
            capability,
            ToolCapabilityProtocol,
        ):
            raise TypeError(
                "tool capability contract required"
            )

        self.capability = capability
        self.execution_count = 0
        self.failure_count = 0

    async def execute(
        self,
        request: ToolExecutionRequest,
    ) -> ToolExecutionResult:
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

        try:
            result = await self.capability.execute(
                request
            )

            if not isinstance(
                result,
                ToolExecutionResult,
            ):
                raise TypeError(
                    "tool capability must return "
                    "ToolExecutionResult"
                )

            if not result.ready():
                raise ValueError(
                    "tool execution result not ready"
                )

            self.execution_count += 1
            return result

        except Exception:
            self.failure_count += 1
            raise

    def ready(self) -> bool:
        return (
            isinstance(
                self.capability,
                ToolCapabilityProtocol,
            )
            and self.capability.ready()
        )

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


__all__ = [
    "ToolExecutionPort",
]
