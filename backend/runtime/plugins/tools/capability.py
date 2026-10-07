from __future__ import annotations

from backend.core.tools.argument_contract import ToolArguments
from backend.core.tools.plugin_contract import ToolPluginProtocol
from backend.core.tools.result_contract import ToolResultProtocol
from backend.core.tools.runtime_tool_protocol import RuntimeToolProtocol
from backend.runtime.tools.runtime import ToolRuntime


class ToolRuntimeCapability:
    """
    Runtime capability facade for canonical ToolRuntime.

    Responsibility:
        - expose the runtime tool execution boundary
        - delegate tool registration and execution
        - expose runtime readiness and diagnostics

    Not Responsible:
        - builtin tool construction
        - application composition
        - tool policy implementation
        - plugin discovery
        - persistence
    """

    VERSION = "1.0"
    NAME = "tools.runtime"

    def __init__(
        self,
        runtime: ToolRuntime,
    ) -> None:
        if not isinstance(
            runtime,
            ToolRuntime,
        ):
            raise TypeError(
                "runtime must ToolRuntime"
            )

        self.runtime = runtime

    @property
    def name(
        self,
    ) -> str:
        return self.NAME

    @property
    def version(
        self,
    ) -> str:
        return self.VERSION

    def capabilities(
        self,
    ) -> tuple[str, ...]:
        return (
            "tool.register",
            "tool.resolve",
            "tool.execute",
        )

    def register_tool(
        self,
        tool: RuntimeToolProtocol,
    ) -> None:
        self.runtime.register_tool(
            tool
        )

    def register_plugin(
        self,
        plugin: ToolPluginProtocol,
    ) -> None:
        self.runtime.register_plugin(
            plugin
        )

    def get_tool(
        self,
        name: str,
    ) -> RuntimeToolProtocol | None:
        return self.runtime.get_tool(
            name
        )

    async def execute(
        self,
        name: str,
        arguments: ToolArguments,
        **kwargs: object,
    ) -> ToolResultProtocol:
        return await self.runtime.execute(
            name,
            arguments,
            **kwargs,
        )

    def ready(
        self,
    ) -> bool:
        return self.runtime.ready()

    def snapshot(
        self,
    ) -> dict[str, int]:
        return self.runtime.snapshot()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "capabilities": self.capabilities(),
            "runtime": self.runtime.dump(),
            "ready": self.ready(),
        }


__all__ = [
    "ToolRuntimeCapability",
]
