from __future__ import annotations

from backend.application.capability.code_modification_proposal import (
    CodeModificationProposal,
)
from backend.application.provider_gateway import (
    ApplicationProviderGatewayProtocol,
)


class CodeModificationProposalFactory:
    VERSION = "1.0"

    def create(
        self,
        *,
        provider: ApplicationProviderGatewayProtocol,
    ) -> CodeModificationProposal:
        if not self.ready():
            raise RuntimeError(
                "code modification proposal factory unavailable"
            )

        proposal = CodeModificationProposal(
            provider
        )

        if not proposal.ready():
            raise RuntimeError(
                "code modification proposal unavailable"
            )

        return proposal

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "CodeModificationProposalFactory",
]
