from __future__ import annotations

from backend.application.capability.code_intelligence_adapter import (
    CodeIntelligenceApplicationCapabilityAdapter,
)
from backend.application.capability.code_intelligence_composition import (
    ApplicationCodeIntelligenceComposition,
)
from backend.application.capability.code_intelligence_composition_factory import (
    ApplicationCodeIntelligenceCompositionFactory,
)
from backend.application.capability.manager import (
    ApplicationCapabilityManager,
)
from backend.application.code_intelligence.service_factory import (
    CodeIntelligenceApplicationServiceFactory,
)
from backend.application.composition.runtime_port import (
    ApplicationRuntimePortProtocol,
)


class CodeIntelligenceStartupBinding:
    """
    Bind the frozen code intelligence stack into application startup.

    Application consumes the Runtime subsystem only through the
    ApplicationRuntimePortProtocol boundary.
    """

    VERSION = "1.2"

    CAPABILITY_KEY = (
        "application.code_intelligence.inspect:1.0"
    )

    def __init__(
        self,
        capability_manager: ApplicationCapabilityManager,
    ) -> None:
        if not isinstance(
            capability_manager,
            ApplicationCapabilityManager,
        ):
            raise TypeError(
                "capability_manager invalid"
            )

        self.composition = (
            ApplicationCodeIntelligenceCompositionFactory()
            .create(
                manager=capability_manager,
            )
        )
        self.capability = None

    def bind(
        self,
        *,
        runtime_port: ApplicationRuntimePortProtocol,
        capability_manager: ApplicationCapabilityManager,
    ) -> CodeIntelligenceApplicationCapabilityAdapter:
        self._validate(
            runtime_port,
            capability_manager,
        )

        self.composition = (
            ApplicationCodeIntelligenceCompositionFactory()
            .create(
                manager=capability_manager,
            )
        )

        runtime_capability = (
            runtime_port.create_code_intelligence_capability()
        )

        service = (
            CodeIntelligenceApplicationServiceFactory()
            .create(
                capability=runtime_capability,
            )
        )

        capability = (
            CodeIntelligenceApplicationCapabilityAdapter(
                service=service,
            )
        )

        installed = self.composition.install(
            capability,
        )

        if installed is not capability:
            raise RuntimeError(
                "installed code intelligence capability mismatch"
            )

        self.composition.enable()

        if not capability.ready():
            raise RuntimeError(
                "code intelligence capability unavailable"
            )

        self.capability = capability

        if not self.ready():
            raise RuntimeError(
                "code intelligence startup binding unavailable"
            )

        return capability

    def reset(
        self,
    ) -> None:
        self.capability = None

    def ready(
        self,
    ) -> bool:
        return bool(
            self.composition.ready()
            and self.capability is not None
            and self.capability.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
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
        runtime_port: ApplicationRuntimePortProtocol,
        capability_manager: ApplicationCapabilityManager,
    ) -> None:
        if not isinstance(
            runtime_port,
            ApplicationRuntimePortProtocol,
        ):
            raise TypeError(
                "runtime port contract required"
            )

        if not isinstance(
            capability_manager,
            ApplicationCapabilityManager,
        ):
            raise TypeError(
                "capability_manager invalid"
            )

        if not capability_manager.ready():
            raise RuntimeError(
                "application capability manager not ready"
            )

        if not runtime_port.ready():
            raise RuntimeError(
                "application runtime port not ready"
            )


__all__ = [
    "CodeIntelligenceStartupBinding",
]
