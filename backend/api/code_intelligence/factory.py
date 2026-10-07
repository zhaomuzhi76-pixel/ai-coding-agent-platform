from __future__ import annotations

from backend.api.code_intelligence.api import CodeIntelligenceAPI
from backend.application.capability.code_intelligence_contract import (
    CodeIntelligenceApplicationCapabilityProtocol,
)


class CodeIntelligenceAPIFactory:
    VERSION = "1.0"

    def create(
        self,
        capability: CodeIntelligenceApplicationCapabilityProtocol,
    ) -> CodeIntelligenceAPI:
        if not self.ready():
            raise RuntimeError(
                "code intelligence api factory unavailable"
            )
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

        api = CodeIntelligenceAPI(capability)

        if not api.ready():
            raise RuntimeError(
                "code intelligence api unavailable"
            )

        return api

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = ["CodeIntelligenceAPIFactory"]
