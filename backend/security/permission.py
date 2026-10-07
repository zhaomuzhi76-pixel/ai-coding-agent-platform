"""Permission point: resource + action."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Permission:
    resource: str
    action: str

    def __post_init__(self) -> None:
        if not self.resource.strip():
            raise ValueError("resource required")
        if not self.action.strip():
            raise ValueError("action required")

    @classmethod
    def parse(cls, raw: str) -> "Permission":
        if ":" not in raw:
            raise ValueError(f"permission must be 'resource:action': {raw}")
        res, _, act = raw.partition(":")
        return cls(resource=res.strip(), action=act.strip())

    def key(self) -> str:
        return f"{self.resource}:{self.action}"

    def matches(self, other: "Permission") -> bool:
        res_ok = other.resource == "*" or self.resource == other.resource
        act_ok = other.action == "*" or self.action == other.action
        return res_ok and act_ok


__all__ = ["Permission"]
