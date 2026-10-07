from __future__ import annotations

from backend.api.code_intelligence.contract import (
    CodeIntelligenceAPIContract,
)
from backend.application.capability.code_intelligence_contract import (
    CodeIntelligenceApplicationCapabilityProtocol,
)
from backend.core.code_intelligence.contracts import (
    CodeIntelligenceRequest,
    CodeIntelligenceResult,
)


class CodeIntelligenceAPI(CodeIntelligenceAPIContract):
    VERSION = "1.0"

    def __init__(
        self,
        capability: CodeIntelligenceApplicationCapabilityProtocol,
    ) -> None:
        if not isinstance(
            capability,
            CodeIntelligenceApplicationCapabilityProtocol,
        ):
            raise TypeError(
                "code intelligence capability contract required"
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

        result = await self.capability.inspect(request)

        if not isinstance(
            result,
            CodeIntelligenceResult,
        ):
            raise TypeError(
                "code intelligence capability returned invalid result"
            )

        self.inspect_count += 1
        return result

    def ready(self) -> bool:
        return (
            isinstance(
                self.capability,
                CodeIntelligenceApplicationCapabilityProtocol,
            )
            and self.capability.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "inspect_count": self.inspect_count,
            "capability": type(self.capability).__name__,
        }


__all__ = ["CodeIntelligenceAPI"]
