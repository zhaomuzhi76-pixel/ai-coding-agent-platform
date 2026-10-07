from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from backend.core.tools.argument_contract import ToolArgumentValue

ToolParameterType = Literal[
    "string",
    "integer",
    "number",
    "boolean",
    "object",
    "array",
]


@dataclass(frozen=True, slots=True)
class ToolParameter:
    name: str
    parameter_type: ToolParameterType
    description: str = ""
    required: bool = True
    default: ToolArgumentValue = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("parameter name required")


@dataclass(frozen=True, slots=True)
class ToolSchema:
    name: str
    description: str
    parameters: tuple[ToolParameter, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("tool name required")

    def parameter(
        self,
        name: str,
    ) -> ToolParameter | None:
        return next(
            (
                item
                for item in self.parameters
                if item.name == name
            ),
            None,
        )


__all__ = [
    "ToolParameter",
    "ToolParameterType",
    "ToolSchema",
]
