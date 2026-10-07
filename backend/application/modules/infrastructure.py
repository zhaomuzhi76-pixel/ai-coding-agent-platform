from __future__ import annotations

from typing import Any

from backend.application.modules.contracts import (
    ApplicationModuleProtocol,
)
from backend.application.modules.infrastructure_composition import (
    ApplicationInfrastructureComposition,
)


class ApplicationInfrastructureModule(
    ApplicationModuleProtocol,
):
    """
    Application infrastructure module boundary.

    Owns:
        - infrastructure lifecycle boundary
        - composition binding

    Does not own:
        - runtime implementation
        - startup orchestration
    """

    VERSION = "3.0"

    def __init__(
        self,
        composition: ApplicationInfrastructureComposition,
    ) -> None:

        if not isinstance(
            composition,
            ApplicationInfrastructureComposition,
        ):
            raise TypeError(
                "invalid infrastructure composition"
            )

        self.composition = composition
        self._started = False

    @property
    def name(
        self,
    ) -> str:
        return "infrastructure"

    @property
    def version(
        self,
    ) -> str:
        return self.VERSION

    def start(
        self,
    ) -> None:

        if not self.composition.ready():
            raise RuntimeError(
                "infrastructure unavailable"
            )

        self._started = True

    def build(
        self,
        context: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "infrastructure": self,
            "runtime": self.resolve(),
        }

    def resolve(
        self,
        name: str | None = None,
    ) -> Any:

        return self.composition.resolve()

    def stop(
        self,
    ) -> None:

        self._started = False

    def ready(
        self,
    ) -> bool:

        return self.composition.ready()

    def dump(
        self,
    ) -> dict[str, object]:

        return {
            "name": self.name,
            "version": self.version,
            "ready": self.ready(),
            "composition": self.composition.dump(),
        }


__all__ = [
    "ApplicationInfrastructureModule",
]
