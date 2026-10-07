from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.code_intelligence.contracts import (
    CodeIntelligenceRequest,
    CodeIntelligenceResult,
)
from backend.application.capability.contracts import (
    ApplicationCapabilityProtocol,
)
from backend.application.code_intelligence.service import (
    CodeIntelligenceApplicationService,
)


@runtime_checkable
class CodeIntelligenceApplicationCapabilityProtocol(
    ApplicationCapabilityProtocol,
    Protocol,
):
    """
    Stable application code intelligence capability.

    Responsibility:
        - expose application-level intelligence inspection
        - return canonical CodeIntelligenceResult

    Not Responsible:
        - runtime plugin construction
        - indexing
        - parsing
        - graph construction
        - persistence
        - transport
    """

    async def inspect(
        self,
        request: CodeIntelligenceRequest,
    ) -> CodeIntelligenceResult:
        ...


__all__ = [
    "CodeIntelligenceApplicationCapabilityProtocol",
]
