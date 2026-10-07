from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.application.capability.contracts import (
    ApplicationCapabilityProtocol,
)
from backend.core.tools.execution_contract import (
    ToolExecutionRequest,
    ToolExecutionResult,
)


@runtime_checkable
class ToolApplicationCapabilityProtocol(
    ApplicationCapabilityProtocol,
    Protocol,
):
    """
    Canonical application tool execution capability.

    Core owns the canonical tool request/result contracts.
    Application owns only the capability lifecycle boundary.
    """

    async def execute(
        self,
        request: ToolExecutionRequest,
    ) -> ToolExecutionResult:
        ...


__all__ = [
    "ToolApplicationCapabilityProtocol",
]
