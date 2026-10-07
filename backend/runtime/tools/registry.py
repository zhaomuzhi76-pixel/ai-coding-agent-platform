from __future__ import annotations

from backend.core.context.context_snapshot_contract import ContextSnapshot
from backend.core.tools.runtime_tool_protocol import RuntimeToolProtocol
from backend.core.tools.tool_registry_protocol import ToolRegistryProtocol


class ToolRegistry(
    ToolRegistryProtocol,
):
    """Runtime tool registry."""

    VERSION = "4.0"

    def __init__(self) -> None:
        self._tools: dict[str, RuntimeToolProtocol] = {}

    def register(
        self,
        name: str,
        tool: RuntimeToolProtocol,
    ) -> None:
        if not name.strip():
            raise ValueError("tool name required")
        if tool is None:
            raise ValueError("tool required")
        if name in self._tools:
            raise ValueError(
                f"tool already registered: {name}"
            )
        self._tools[name] = tool

    def get(
        self,
        name: str,
    ) -> RuntimeToolProtocol | None:
        if not name.strip():
            return None
        return self._tools.get(name)

    def remove(
        self,
        name: str,
    ) -> None:
        if not name.strip():
            raise ValueError("tool name required")
        self._tools.pop(name, None)

    def names(self) -> list[str]:
        return list(self._tools)

    def all(self) -> dict[str, RuntimeToolProtocol]:
        return dict(self._tools)

    def ready(self) -> bool:
        return True

    def dump(self) -> ContextSnapshot:
        return {
            "name": "ToolRegistry",
            "version": self.VERSION,
            "responsibility": (
                "runtime_tool_registry",
            ),
            "ready": self.ready(),
        }


RuntimeToolRegistry = ToolRegistry

__all__ = [
    "ToolRegistry",
    "RuntimeToolRegistry",
]
