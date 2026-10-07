from __future__ import annotations

from typing import Any

from backend.application.capability.descriptor import (
    ApplicationCapabilityDescriptor,
)
from backend.application.capability.manager import (
    ApplicationCapabilityManager,
)


class ApplicationToolComposition:
    """
    Canonical application tool capability composition.

    Owns:
        - tool capability installation
        - tool capability lifecycle
        - tool capability resolution
    """

    VERSION = "1.0"
    CAPABILITY_NAME = "tools.execution"
    DESCRIPTOR = ApplicationCapabilityDescriptor(
        name=CAPABILITY_NAME,
        version=VERSION,
        category="application",
        capabilities=("tool.execute",),
    )

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
    ) -> None:
        self.manager.install(
            self.DESCRIPTOR,
            implementation,
            context,
        )

    def enable(
        self,
        context: Any = None,
    ) -> None:
        self.manager.enable(
            self.DESCRIPTOR.key(),
            context,
        )

    def disable(self) -> None:
        self.manager.disable(
            self.DESCRIPTOR.key(),
        )

    def unload(self) -> None:
        self.manager.unload(
            self.DESCRIPTOR.key(),
        )

    def resolve(self) -> Any:
        return self.manager.resolve(
            self.DESCRIPTOR.key(),
        )

    def ready(self) -> bool:
        return self.manager.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "capability": self.CAPABILITY_NAME,
            "descriptor": self.DESCRIPTOR.key(),
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationToolComposition",
]
