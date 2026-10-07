from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol
from backend.core.tools.argument_contract import ToolArguments
from backend.core.tools.result_contract import ToolResultProtocol


@runtime_checkable
class RuntimeToolProtocol(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Runtime tool capability boundary.
    """

    name: str
    description: str

    async def execute(
        self,
        arguments: ToolArguments,
    ) -> ToolResultProtocol:
        ...


__all__ = [
    "RuntimeToolProtocol",
]
