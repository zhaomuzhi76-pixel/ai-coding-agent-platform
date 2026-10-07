from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ToolAliasProtocol(
    Protocol,
):
    """Standard tool alias resolution contract."""

    def resolve(
        self,
        name: str,
    ) -> str:
        ...


__all__ = [
    "ToolAliasProtocol",
]
