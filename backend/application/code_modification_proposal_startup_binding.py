from __future__ import annotations

from backend.application.capability.code_modification_proposal_adapter import (
    CodeModificationProposalAdapter,
)
from backend.application.capability.code_modification_proposal_binding import (
    CodeModificationProposalBinding,
)
from backend.application.capability.manager import (
    ApplicationCapabilityManager,
)
from backend.application.provider_gateway.contracts import (
    ApplicationProviderRuntimeProtocol,
)
from backend.application.composition.provider_factory import (
    ApplicationProviderCompositionFactory,
)


class CodeModificationProposalStartupBinding:
    VERSION = "1.0"

    def __init__(
        self,
        capability_manager: ApplicationCapabilityManager,
    ) -> None:
        if capability_manager is None:
            raise ValueError(
                "capability manager required"
            )

        if not capability_manager.ready():
            raise RuntimeError(
                "capability manager unavailable"
            )

        self.capability_manager = capability_manager
        self.capability = None

    def bind(
        self,
        *,
        provider_runtime: ApplicationProviderRuntimeProtocol,
    ) -> CodeModificationProposalAdapter:
        if not isinstance(
            provider_runtime,
            ApplicationProviderRuntimeProtocol,
        ):
            raise TypeError(
                "provider runtime contract required"
            )

        if not provider_runtime.ready():
            raise RuntimeError(
                "provider runtime unavailable"
            )

        provider_gateway = (
            ApplicationProviderCompositionFactory()
            .create(
                runtime=provider_runtime,
            )
            .create()
        )

        capability = CodeModificationProposalBinding().bind(
            manager=self.capability_manager,
            provider=provider_gateway,
        )

        self.capability = capability

        if not capability.ready():
            raise RuntimeError(
                "code modification proposal unavailable"
            )

        return capability

    def ready(self) -> bool:
        return (
            self.capability_manager.ready()
            and (
                self.capability is None
                or self.capability.ready()
            )
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "capability": (
                type(self.capability).__name__
                if self.capability is not None
                else None
            ),
        }


__all__ = [
    "CodeModificationProposalStartupBinding",
]
