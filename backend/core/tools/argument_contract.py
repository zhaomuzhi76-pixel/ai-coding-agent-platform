from __future__ import annotations

from typing import Protocol, TypeAlias, runtime_checkable

ToolArgumentValue: TypeAlias = (
    str
    | int
    | float
    | bool
    | None
    | list["ToolArgumentValue"]
    | dict[str, "ToolArgumentValue"]
)

ToolArguments = dict[str, ToolArgumentValue]


@runtime_checkable
class ToolArgumentProtocol(Protocol):
    def resolve(
        self,
        tool_name: str,
        arguments: ToolArguments,
    ) -> ToolArguments:
        ...


__all__ = [
    "ToolArgumentProtocol",
    "ToolArgumentValue",
    "ToolArguments",
]
