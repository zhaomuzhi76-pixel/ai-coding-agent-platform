from __future__ import annotations

from backend.core.context.context_snapshot_contract import ContextSnapshot
from backend.core.tools.alias_contract import ToolAliasProtocol


class ToolAliasResolver(
    ToolAliasProtocol,
):
    """Runtime tool alias resolver."""

    VERSION = "2.0"

    DEFAULT_ALIASES = {
        "writer": "file_write",
        "write": "file_write",
        "reader": "file_read",
        "read": "file_read",
        "scan": "workspace_scan",
        "compile": "terminal",
    }

    def __init__(
        self,
        aliases: dict[str, str] | None = None,
    ) -> None:
        self._aliases = dict(self.DEFAULT_ALIASES)
        if aliases:
            self._aliases.update(aliases)

    def resolve(
        self,
        name: str,
    ) -> str:
        if not name.strip():
            raise ValueError("tool name required")
        return self._aliases.get(name, name)

    def register(
        self,
        alias: str,
        tool_name: str,
    ) -> None:
        if not alias.strip():
            raise ValueError("alias required")
        if not tool_name.strip():
            raise ValueError("tool name required")
        self._aliases[alias] = tool_name

    def remove(
        self,
        alias: str,
    ) -> None:
        if not alias.strip():
            raise ValueError("alias required")
        self._aliases.pop(alias, None)

    def ready(self) -> bool:
        return True

    def dump(self) -> ContextSnapshot:
        return {
            "name": "ToolAliasResolver",
            "version": self.VERSION,
            "responsibility": (
                "runtime_tool_alias_resolution",
            ),
            "ready": self.ready(),
        }


__all__ = [
    "ToolAliasResolver",
]
