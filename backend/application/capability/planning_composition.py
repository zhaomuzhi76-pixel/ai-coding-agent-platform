from __future__ import annotations

from typing import Any

from backend.application.capability.descriptor import (
    ApplicationCapabilityDescriptor,
)
from backend.application.capability.manager import (
    ApplicationCapabilityManager,
)


class ApplicationPlanningCapabilityComposition:
    """
    Planning capability lifecycle composition boundary.

    Owns:
        - planning capability installation
        - lifecycle delegation
        - capability resolution

    Does not own:
        - planner implementation
        - runtime construction
        - planning algorithm
        - execution lifecycle
    """

    VERSION = "1.0"

    CAPABILITY_NAME = "planning"

    def __init__(
        self,
        manager: ApplicationCapabilityManager,
    ) -> None:
        if not isinstance(
            manager,
            ApplicationCapabilityManager,
        ):
            raise TypeError(
                "manager must ApplicationCapabilityManager"
            )

        if not manager.ready():
            raise RuntimeError(
                "capability manager unavailable"
            )

        self.manager = manager

    def install(
        self,
        implementation: Any,
        context: Any = None,
    ) -> Any:

        descriptor = ApplicationCapabilityDescriptor(
            name=self.CAPABILITY_NAME,
            version=self.VERSION,
            category="application",
        )

        return self.manager.install(
            descriptor,
            implementation,
            context,
        )

    def enable(
        self,
        context: Any = None,
    ) -> None:
        self.manager.enable(
            self.CAPABILITY_NAME,
            context,
        )

    def disable(
        self,
    ) -> None:
        self.manager.disable(
            self.CAPABILITY_NAME,
        )

    def unload(
        self,
    ) -> None:
        self.manager.unload(
            self.CAPABILITY_NAME,
        )

    def resolve(
        self,
    ) -> Any:
        return self.manager.resolve(
            self.identity(),
        )

    def identity(
        self,
    ) -> str:
        return (
            f"{self.CAPABILITY_NAME}."
            f"{self.CAPABILITY_NAME}:"
            f"{self.VERSION}"
        )

    def ready(
        self,
    ) -> bool:
        return self.manager.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "capability": self.CAPABILITY_NAME,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationPlanningCapabilityComposition",
]
