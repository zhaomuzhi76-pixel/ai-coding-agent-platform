from __future__ import annotations

from typing import Any

from backend.application.capability.tool_composition import (
    ApplicationToolComposition,
)
from backend.application.modules.contracts import (
    ApplicationModuleProtocol,
)


class ApplicationToolModule(ApplicationModuleProtocol):
    """
    Application tool module lifecycle projection.

    Capability ownership remains in ApplicationToolComposition.
    """

    VERSION = "3.0"
    name = "tool"
    version = VERSION

    def __init__(
        self,
        composition: ApplicationToolComposition,
    ) -> None:
        if not isinstance(
            composition,
            ApplicationToolComposition,
        ):
            raise TypeError(
                "invalid tool composition"
            )
        self.composition = composition
        self._started = False

    def start(self) -> None:
        if not self.composition.ready():
            raise RuntimeError(
                "tool composition unavailable"
            )
        self._started = True

    def build(
        self,
        context: dict[str, Any],
    ) -> dict[str, object]:
        return {"tool": self}

    def resolve(
        self,
        name: str | None = None,
    ) -> Any:
        return self.composition if name is None else (
            self.composition.resolve(name)
        )

    def stop(self) -> None:
        self._started = False

    def ready(self) -> bool:
        return self.composition.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "ready": self.ready(),
            "composition": self.composition.dump(),
        }


__all__ = ["ApplicationToolModule"]
