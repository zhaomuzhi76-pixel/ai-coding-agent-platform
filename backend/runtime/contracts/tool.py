from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.tools.runtime_tool_protocol import (
    RuntimeToolProtocol,
)
from backend.core.tools.schema import ToolSchema


@runtime_checkable
class RuntimeToolContractProtocol(
    RuntimeToolProtocol,
    Protocol,
):
    """Runtime executable tool contract."""

    def schema(self) -> ToolSchema:
        ...


__all__ = ["RuntimeToolContractProtocol"]
