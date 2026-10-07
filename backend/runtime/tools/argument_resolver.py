from __future__ import annotations

from backend.core.context.context_snapshot_contract import ContextSnapshot
from backend.core.tools.argument_contract import (
    ToolArgumentProtocol,
    ToolArguments,
)


class ToolArgumentResolver(
    ToolArgumentProtocol,
):
    """Normalize runtime tool arguments."""

    VERSION = "3.0"

    def resolve(
        self,
        tool_name: str,
        arguments: ToolArguments,
    ) -> ToolArguments:
        if not tool_name.strip():
            raise ValueError("tool name required")

        payload = dict(arguments)

        if tool_name == "terminal":
            return self._resolve_terminal(payload)

        return payload

    def _resolve_terminal(
        self,
        arguments: ToolArguments,
    ) -> ToolArguments:
        if "command" in arguments:
            return arguments

        command = arguments.get("cmd")

        if isinstance(command, str):
            arguments["command"] = command
            arguments.pop("cmd", None)

        return arguments

    def ready(self) -> bool:
        return True

    def dump(self) -> ContextSnapshot:
        return {
            "name": "ToolArgumentResolver",
            "version": self.VERSION,
            "responsibility": (
                "runtime_tool_argument_resolution",
            ),
            "ready": self.ready(),
        }


__all__ = [
    "ToolArgumentResolver",
]
