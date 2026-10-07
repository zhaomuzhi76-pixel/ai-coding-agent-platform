from __future__ import annotations

from typing import Any

from backend.core.code_intelligence.contracts import (
    CodeIntelligenceRequest,
    CodeIntelligenceResult,
)
from backend.application.capability.code_intelligence_contract import (
    CodeIntelligenceApplicationCapabilityProtocol,
)
from backend.application.code_intelligence.service import (
    CodeIntelligenceApplicationService,
)


class CodeIntelligenceApplicationCapabilityAdapter(
    CodeIntelligenceApplicationCapabilityProtocol,
):
    """
    Application capability adapter for code intelligence.

    Responsibility:
        - own application capability identity
        - delegate inspection to application service
        - expose application lifecycle state

    Not Responsible:
        - runtime capability construction
        - indexing
        - parsing
        - graph construction
        - persistence
    """

    VERSION = "1.0"
    NAME = "code_intelligence.inspect"

    def __init__(
        self,
        service: CodeIntelligenceApplicationService,
    ) -> None:
        if service is None:
            raise ValueError(
                "code intelligence service required"
            )

        if not isinstance(
            service,
            CodeIntelligenceApplicationService,
        ):
            raise TypeError(
                "service must be "
                "CodeIntelligenceApplicationService"
            )

        self.service = service
        self.initialized = False
        self.shutdown_count = 0

    @property
    def name(
        self,
    ) -> str:
        return self.NAME

    @property
    def version(
        self,
    ) -> str:
        return self.VERSION

    def capabilities(
        self,
    ) -> tuple[str, ...]:
        return (
            "code.inspect",
            "code.project",
            "code.file",
            "code.analysis",
            "code.impact",
            "code.context",
            "code.index",
        )

    async def inspect(
        self,
        request: CodeIntelligenceRequest,
    ) -> CodeIntelligenceResult:
        if not self.initialized:
            raise RuntimeError(
                "code intelligence capability not enabled"
            )

        return await self.service.inspect(
            request
        )

    def initialize(
        self,
        context: Any = None,
    ) -> None:
        if not self.service.ready():
            raise RuntimeError(
                "code intelligence service not ready"
            )

        self.initialized = True

    def shutdown(
        self,
    ) -> None:
        self.initialized = False
        self.shutdown_count += 1

    def ready(
        self,
    ) -> bool:
        return self.service.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "capabilities": self.capabilities(),
            "initialized": self.initialized,
            "shutdown_count": self.shutdown_count,
            "service": type(
                self.service
            ).__name__,
            "service_ready": self.service.ready(),
            "ready": self.ready(),
        }


__all__ = [
    "CodeIntelligenceApplicationCapabilityAdapter",
]
