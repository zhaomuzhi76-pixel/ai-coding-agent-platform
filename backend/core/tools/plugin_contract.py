from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.protocols.dumpable import (
    DumpableProtocol,
)

from backend.core.protocols.ready import (
    ReadyProtocol,
)

from backend.core.tools.runtime_tool_protocol import (
    RuntimeToolProtocol,
)


@runtime_checkable
class ToolPluginProtocol(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Runtime tool plugin contract.

    Responsibility:

        - provide runtime tools
        - expose plugin identity
        - expose plugin readiness

    Not Responsible:

        - tool execution
        - tool registry management
        - tool lifecycle management
        - capability discovery
        - persistence
    """

    name: str

    def tools(
        self,
    ) -> tuple[
        RuntimeToolProtocol,
        ...,
    ]:
        ...


__all__ = [
    "ToolPluginProtocol",
]
