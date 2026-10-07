from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol
from backend.core.tools.runtime_tool_protocol import (
    RuntimeToolProtocol,
)


@runtime_checkable
class ToolRegistryProtocol(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):

    def register(
        self,
        name: str,
        tool: RuntimeToolProtocol,
    ) -> None:
        ...

    def get(
        self,
        name: str,
    ) -> RuntimeToolProtocol | None:
        ...

    def remove(
        self,
        name: str,
    ) -> None:
        ...

    def names(
        self,
    ) -> list[str]:
        ...


__all__ = [
    "ToolRegistryProtocol",
]
