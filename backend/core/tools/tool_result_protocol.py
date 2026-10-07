from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.protocols.ready import ReadyProtocol
from backend.core.tools.argument_contract import (
    ToolArgumentValue,
)


@runtime_checkable
class ToolResultProtocol(
    ReadyProtocol,
    Protocol,
):

    success: bool
    tool_name: str
    output: ToolArgumentValue
    error: str | None


__all__ = [
    "ToolResultProtocol",
]
