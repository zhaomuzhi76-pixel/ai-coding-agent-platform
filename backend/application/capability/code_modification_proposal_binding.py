from __future__ import annotations

from backend.application.capability.code_modification_proposal import (
    CodeModificationProposal,
)
from backend.application.capability.code_modification_proposal_adapter import (
    CodeModificationProposalAdapter,
)
from backend.application.capability.descriptor import (
    ApplicationCapabilityDescriptor,
)
from backend.application.capability.manager import (
    ApplicationCapabilityManager,
)
from backend.application.capability.code_modification_proposal_factory import (
    CodeModificationProposalFactory,
)
from backend.application.provider_gateway import (
    ApplicationProviderGatewayProtocol,
)


class CodeModificationProposalBinding:
    VERSION = "1.0"

    DESCRIPTOR = ApplicationCapabilityDescriptor(
        name="code_modification.propose",
        version="1.0",
        category="application",
        capabilities=(
            "code.modification.propose",
            "code.modification.change",
        ),
    )

    def bind(
        self,
        *,
        manager: ApplicationCapabilityManager,
        provider: ApplicationProviderGatewayProtocol,
    ) -> CodeModificationProposalAdapter:
        if manager is None or not manager.ready():
            raise RuntimeError(
                "capability manager not ready"
            )

        if not isinstance(
            provider,
            ApplicationProviderGatewayProtocol,
        ):
            raise TypeError(
                "provider gateway contract required"
            )

        proposal = CodeModificationProposalFactory().create(
            provider=provider,
        )

        capability = CodeModificationProposalAdapter(
            proposal
        )

        installed = manager.install(
            descriptor=self.DESCRIPTOR,
            implementation=capability,
        )

        if installed is not capability:
            raise RuntimeError(
                "installed proposal capability mismatch"
            )

        manager.enable(
            self.DESCRIPTOR.name
        )

        if not capability.ready():
            raise RuntimeError(
                "code modification proposal unavailable"
            )

        return capability

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "capability": self.DESCRIPTOR.key(),
            "ready": self.ready(),
        }


__all__ = [
    "CodeModificationProposalBinding",
]
