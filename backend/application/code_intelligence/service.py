from __future__ import annotations

from backend.core.code_intelligence.contracts import (
    CodeIntelligenceCapabilityProtocol,
    CodeIntelligenceRequest,
    CodeIntelligenceResult,
)


class CodeIntelligenceApplicationService:
    """
    Application-owned code intelligence service.

    Responsibility:
        - consume runtime code intelligence capability
        - expose application inspection operations
        - preserve stable request/result contracts

    Not Responsible:
        - indexing
        - parsing
        - graph construction
        - intelligence implementation
        - plugin lifecycle
        - transport
    """

    VERSION = "1.0"

    def __init__(
        self,
        capability: CodeIntelligenceCapabilityProtocol,
    ) -> None:
        if capability is None:
            raise ValueError(
                "code intelligence capability required"
            )

        if not isinstance(
            capability,
            CodeIntelligenceCapabilityProtocol,
        ):
            raise TypeError(
                "capability must implement "
                "CodeIntelligenceCapabilityProtocol"
            )

        if not capability.ready():
            raise RuntimeError(
                "code intelligence capability not ready"
            )

        self.capability = capability
        self.inspect_count = 0

    async def inspect(
        self,
        request: CodeIntelligenceRequest,
    ) -> CodeIntelligenceResult:
        if not isinstance(
            request,
            CodeIntelligenceRequest,
        ):
            raise TypeError(
                "request must CodeIntelligenceRequest"
            )

        if not request.ready():
            raise ValueError(
                "code intelligence request not ready"
            )

        result = await self.capability.inspect(
            request
        )

        if not isinstance(
            result,
            CodeIntelligenceResult,
        ):
            raise TypeError(
                "code intelligence capability must return "
                "CodeIntelligenceResult"
            )

        if not result.ready():
            raise RuntimeError(
                "code intelligence result not ready"
            )

        self.inspect_count += 1
        return result

    def ready(
        self,
    ) -> bool:
        return (
            isinstance(
                self.capability,
                CodeIntelligenceCapabilityProtocol,
            )
            and self.capability.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "inspect_count": self.inspect_count,
            "capability": type(
                self.capability
            ).__name__,
        }


__all__ = [
    "CodeIntelligenceApplicationService",
]
