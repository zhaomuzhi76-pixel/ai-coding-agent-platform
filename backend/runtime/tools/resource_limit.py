from __future__ import annotations

from dataclasses import dataclass

from backend.core.tools.argument_contract import ToolArgumentValue


@dataclass(frozen=True, slots=True)
class ResourceLimits:
    timeout: float | None = None
    max_input_size: int | None = None
    max_output_size: int | None = None

    def __post_init__(self) -> None:
        if self.timeout is not None and self.timeout <= 0:
            raise ValueError("timeout must be positive")

        for value in (
            self.max_input_size,
            self.max_output_size,
        ):
            if value is not None and value < 0:
                raise ValueError(
                    "size limit cannot be negative"
                )


class ResourceLimit:
    """Tool resource constraint store."""

    VERSION = "3.0"

    def __init__(self) -> None:
        self._limits: dict[str, ResourceLimits] = {}

    def set_limit(
        self,
        tool_name: str,
        timeout: float | None = None,
        max_input_size: int | None = None,
        max_output_size: int | None = None,
    ) -> None:
        if not tool_name.strip():
            raise ValueError("tool name required")

        self._limits[tool_name] = ResourceLimits(
            timeout=timeout,
            max_input_size=max_input_size,
            max_output_size=max_output_size,
        )

    def get_limit(
        self,
        tool_name: str,
    ) -> ResourceLimits | None:
        if not tool_name.strip():
            raise ValueError("tool name required")

        return self._limits.get(tool_name)

    def check_input_size(
        self,
        tool_name: str,
        size: int,
    ) -> bool:
        if size < 0:
            raise ValueError("size cannot be negative")

        limit = self.get_limit(tool_name)

        return (
            limit is None
            or limit.max_input_size is None
            or size <= limit.max_input_size
        )

    def check_output_size(
        self,
        tool_name: str,
        size: int,
    ) -> bool:
        if size < 0:
            raise ValueError("size cannot be negative")

        limit = self.get_limit(tool_name)

        return (
            limit is None
            or limit.max_output_size is None
            or size <= limit.max_output_size
        )

    def timeout(
        self,
        tool_name: str,
    ) -> float | None:
        limit = self.get_limit(tool_name)

        return (
            None
            if limit is None
            else limit.timeout
        )

    def remove(
        self,
        tool_name: str,
    ) -> None:
        if not tool_name.strip():
            raise ValueError("tool name required")

        self._limits.pop(tool_name, None)

    def clear(self) -> None:
        self._limits.clear()

    def ready(self) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, ToolArgumentValue]:
        return {
            "name": "ResourceLimit",
            "version": self.VERSION,
            "ready": self.ready(),
            "count": len(self._limits),
        }


__all__ = [
    "ResourceLimit",
    "ResourceLimits",
]
