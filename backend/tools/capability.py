from __future__ import annotations

from dataclasses import dataclass, field

from backend.core.tools.argument_contract import ToolArgumentValue


@dataclass(frozen=True, slots=True)
class ToolCapability:
    name: str
    description: str = ""
    actions: tuple[str, ...] = ()
    constraints: dict[str, ToolArgumentValue] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("capability name required")

        if any(not action.strip() for action in self.actions):
            raise ValueError("capability action cannot be empty")

    def supports(self, action: str) -> bool:
        if not action.strip():
            return False
        return action in self.actions

    def dump(self) -> dict[str, ToolArgumentValue]:
        return {
            "name": self.name,
            "description": self.description,
            "actions": list(self.actions),
            "constraints": dict(self.constraints),
        }


__all__ = [
    "ToolCapability",
]
