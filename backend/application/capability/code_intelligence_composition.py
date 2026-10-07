from __future__ import annotations

from typing import Any

from backend.application.capability.descriptor import (
    ApplicationCapabilityDescriptor,
)
from backend.application.capability.manager import (
    ApplicationCapabilityManager,
)


class ApplicationCodeIntelligenceComposition:
    """
    Canonical application code-intelligence capability composition.
    """

    VERSION = "1.0"
    CAPABILITY_NAME = "code_intelligence.inspect"

    DESCRIPTOR = ApplicationCapabilityDescriptor(
        name=CAPABILITY_NAME,
        version=VERSION,
        category="application",
        capabilities=(
            "code.inspect",
            "code.project",
            "code.file",
            "code.analysis",
            "code.impact",
            "code.context",
            "code.index",
        ),
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
                "manager must be ApplicationCapabilityManager"
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
        installed = self.manager.install(
            self.DESCRIPTOR,
            implementation,
            context,
        )

        if installed is None:
            raise RuntimeError(
                "code intelligence capability installation failed"
            )

        return installed

    def enable(
        self,
        context: Any = None,
    ) -> None:
        self.manager.enable(
            self.CAPABILITY_NAME,
            context,
        )

        state = self.manager.state(
            self.CAPABILITY_NAME
        )

        if state.value != "enabled":
            raise RuntimeError(
                "code intelligence capability not enabled"
            )

    def disable(
        self,
    ) -> None:
        self.manager.disable(
            self.CAPABILITY_NAME
        )

    def unload(
        self,
    ) -> None:
        self.manager.unload(
            self.CAPABILITY_NAME
        )

    def resolve(
        self,
    ) -> Any:
        return self.manager.resolve(
            self.CAPABILITY_NAME
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
            "descriptor": self.DESCRIPTOR.key(),
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationCodeIntelligenceComposition",
]
