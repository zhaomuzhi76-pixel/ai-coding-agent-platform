from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from backend.core.tools.argument_contract import (
    ToolArgumentValue,
)
from backend.core.tools.tool_result_protocol import (
    ToolResultProtocol,
)


@dataclass(frozen=True, slots=True)
class ToolResult:
    success: bool
    tool_name: str
    output: ToolArgumentValue = None
    error: str | None = None
    metadata: dict[str, ToolArgumentValue] = field(
        default_factory=dict
    )
    created_at: str = field(
        default_factory=lambda: datetime.now(
            ZoneInfo("Asia/Shanghai")
        ).isoformat()
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.tool_name,
            str,
        ) or not self.tool_name.strip():
            raise ValueError(
                "tool_name required"
            )

        if self.success and self.error is not None:
            raise ValueError(
                "successful result cannot contain error"
            )

        if not self.success and not self.error:
            raise ValueError(
                "failed result requires error"
            )

    @classmethod
    def success_result(
        cls,
        tool_name: str,
        output: ToolArgumentValue = None,
        metadata: dict[str, ToolArgumentValue] | None = None,
    ) -> "ToolResult":
        return cls(
            success=True,
            tool_name=tool_name,
            output=output,
            metadata=dict(metadata or {}),
        )

    @classmethod
    def failure_result(
        cls,
        tool_name: str,
        error: str,
        metadata: dict[str, ToolArgumentValue] | None = None,
    ) -> "ToolResult":
        return cls(
            success=False,
            tool_name=tool_name,
            error=error,
            metadata=dict(metadata or {}),
        )

    def ready(
        self,
    ) -> bool:
        return bool(
            self.tool_name.strip()
        )


__all__ = [
    "ToolResult",
    "ToolResultProtocol",
]
