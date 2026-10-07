from __future__ import annotations

from typing import Any

from backend.application.modules.contracts import (
    ApplicationModuleProtocol,
)


class ApplicationAgentSupport:
    """
    Agent support capability boundary.

    Owns:
        - agent support state
        - support metadata

    Does not own:
        - agent implementation
        - planner implementation
        - execution runtime
    """

    VERSION = "1.0"

    name = "application_agent_support"
    version = VERSION

    def __init__(self) -> None:
        self._items: dict[str, Any] = {}
        self._ready = True

    def register(
        self,
        name: str,
        value: Any,
    ) -> None:
        if not name:
            raise ValueError(
                "support name required"
            )

        if value is None:
            raise ValueError(
                "support value required"
            )

        if name in self._items:
            raise ValueError(
                f"support already exists: {name}"
            )

        self._items[name] = value

    def resolve(
        self,
        name: str,
    ) -> Any:
        if name not in self._items:
            raise LookupError(
                f"support not found: {name}"
            )

        return self._items[name]

    def names(
        self,
    ) -> tuple[str, ...]:
        return tuple(self._items)

    def ready(
        self,
    ) -> bool:
        return self._ready

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "supports": self.names(),
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationAgentSupport",
]
