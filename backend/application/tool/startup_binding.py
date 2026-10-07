from __future__ import annotations

from typing import Any

from backend.application.capability.manager import (
    ApplicationCapabilityManager,
)
from backend.application.capability.tool_adapter import (
    ToolApplicationCapabilityAdapter,
)
from backend.application.capability.tool_composition import (
    ApplicationToolComposition,
)
from backend.application.capability.tool_composition_factory import (
    ApplicationToolCompositionFactory,
)


class ToolApplicationStartupBinding:
    """
    Bind the prepared tool application capability into startup.

    Responsibility:
        - install prepared capability
        - enable capability lifecycle
        - expose startup readiness
        - reset binding state

    Not Responsible:
        - tool runtime construction
        - builtin registration
        - plugin discovery
        - tool execution
        - application module construction
    """

    VERSION = "1.0"
    CAPABILITY_KEY = (
        "application.tools.execution:1.0"
    )

    def __init__(
        self,
        composition: ApplicationToolComposition,
    ) -> None:

        if not isinstance(
            composition,
            ApplicationToolComposition,
        ):
            raise TypeError(
                "composition must be ApplicationToolComposition"
            )

        self.composition = composition

        self.capability: (
            ToolApplicationCapabilityAdapter
            | None
        ) = None

    def bind(
        self,
        *,
        capability_manager: ApplicationCapabilityManager,
        capability: ToolApplicationCapabilityAdapter,
    ) -> ToolApplicationCapabilityAdapter:
        self._validate(
            capability_manager,
            capability,
        )

        installed = capability_manager.install(
            descriptor=self.composition.DESCRIPTOR,
            implementation=capability,
        )

        if installed is not capability:
            raise RuntimeError(
                "installed tool capability mismatch"
            )

        capability_manager.enable(
            self.composition.DESCRIPTOR.name
        )

        if (
            capability_manager.state(
                self.composition.DESCRIPTOR.name
            ).value
            != "enabled"
        ):
            raise RuntimeError(
                "tool application capability not enabled"
            )

        self.capability = capability

        if not self.ready():
            raise RuntimeError(
                "tool application startup binding unavailable"
            )

        return capability

    def reset(self) -> None:
        self.capability = None

    def ready(self) -> bool:
        return bool(
            self.composition.ready()
            and self.capability is not None
            and self.capability.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "capability_key": self.CAPABILITY_KEY,
            "capability": (
                type(self.capability).__name__
                if self.capability is not None
                else None
            ),
            "ready": self.ready(),
        }

    @staticmethod
    def _validate(
        capability_manager: Any,
        capability: Any,
    ) -> None:
        if not isinstance(
            capability_manager,
            ApplicationCapabilityManager,
        ):
            raise TypeError(
                "capability_manager must "
                "ApplicationCapabilityManager"
            )

        if not capability_manager.ready():
            raise RuntimeError(
                "application capability manager not ready"
            )

        if not isinstance(
            capability,
            ToolApplicationCapabilityAdapter,
        ):
            raise TypeError(
                "capability must "
                "ToolApplicationCapabilityAdapter"
            )

        if not capability.ready():
            raise RuntimeError(
                "tool application capability not ready"
            )


__all__ = [
    "ToolApplicationStartupBinding",
]
