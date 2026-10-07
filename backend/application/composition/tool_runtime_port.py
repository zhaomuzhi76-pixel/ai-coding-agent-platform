from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.tools.argument_contract import ToolArguments
from backend.core.tools.result_contract import ToolResultProtocol


@runtime_checkable
class ApplicationToolRuntimeProtocol(
    Protocol,
):
    """
    Application-visible boundary for runtime tool execution.

    Application may execute and inspect the capability, but may not
    construct, discover, register, or mutate runtime tools.
    """

    @property
    def name(
        self,
    ) -> str:
        ...

    @property
    def version(
        self,
    ) -> str:
        ...

    async def execute(
        self,
        name: str,
        arguments: ToolArguments,
        **kwargs: object,
    ) -> ToolResultProtocol:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def snapshot(
        self,
    ) -> dict[str, int]:
        ...

    def dump(
        self,
    ) -> dict[str, object]:
        ...


__all__ = [
    "ApplicationToolRuntimeProtocol",
]
