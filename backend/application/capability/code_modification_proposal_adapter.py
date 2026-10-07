from __future__ import annotations

from typing import Any

from backend.application.capability.code_modification_proposal import (
    CodeModificationProposal,
)
from backend.application.capability.contracts import (
    ApplicationCapabilityProtocol,
)


class CodeModificationProposalAdapter(
    ApplicationCapabilityProtocol,
):
    NAME = "code_modification.propose"
    VERSION = "1.0"

    def __init__(
        self,
        proposal: CodeModificationProposal,
    ) -> None:
        if not isinstance(
            proposal,
            CodeModificationProposal,
        ):
            raise TypeError(
                "proposal must CodeModificationProposal"
            )

        self.proposal = proposal
        self.initialized = False
        self.shutdown_count = 0

    @property
    def name(self) -> str:
        return self.NAME

    @property
    def version(self) -> str:
        return self.VERSION

    def capabilities(self) -> tuple[str, ...]:
        return (
            "code.modification.propose",
            "code.modification.change",
        )

    async def propose(
        self,
        *,
        task: str,
        file: str,
        source: str,
        provider: str,
        model: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, object]:
        if not self.initialized:
            raise RuntimeError(
                "code modification proposal not enabled"
            )

        return await self.proposal.propose(
            task=task,
            file=file,
            source=source,
            provider=provider,
            model=model,
            context=context,
        )

    def initialize(
        self,
        context: Any = None,
    ) -> None:
        if not self.proposal.ready():
            raise RuntimeError(
                "code modification proposal unavailable"
            )

        self.initialized = True

    def shutdown(self) -> None:
        self.initialized = False
        self.shutdown_count += 1

    def ready(self) -> bool:
        return self.proposal.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "capabilities": self.capabilities(),
            "initialized": self.initialized,
            "shutdown_count": self.shutdown_count,
            "proposal": self.proposal.dump(),
            "ready": self.ready(),
        }


__all__ = [
    "CodeModificationProposalAdapter",
]
