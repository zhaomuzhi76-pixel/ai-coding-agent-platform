from __future__ import annotations

from typing import Any, Dict

from backend.agent.planner.builder_registry_defaults import (
    register_defaults,
)


class BuilderRegistry:
    """
    Planner builder 容器。

    Responsibility: 注册 / 查找 builder。
    Not Responsible: routing / workflow / execution。
    """

    VERSION = "7.0"
    RESPONSIBILITY = ("builder_instance_registry",)

    def __init__(self) -> None:
        self.builders: Dict[str, Any] = {}
        register_defaults(self)

    def register(self, name: str, builder: Any) -> None:
        if not name:
            raise ValueError("builder name required")
        if not hasattr(builder, "build"):
            raise TypeError("builder must implement build()")
        if name in self.builders:
            raise RuntimeError(f"builder exists: {name}")
        self.builders[name] = builder

    def get(self, name: str) -> Any | None:
        return self.builders.get(name)

    def exists(self, name: str) -> bool:
        return name in self.builders

    def ready(self) -> bool:
        return bool(self.builders)

    def validate(self) -> bool:
        return all(
            hasattr(b, "build") for b in self.builders.values()
        )

    def dump(self) -> Dict[str, Any]:
        return {
            "name": "BuilderRegistry",
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "valid": self.validate(),
            "builders": list(self.builders.keys()),
        }


__all__ = ["BuilderRegistry"]
