from __future__ import annotations

from backend.core.code_intelligence.contracts import (
    CodeIntelligenceCapabilityProtocol,
)
from backend.application.code_intelligence.service import (
    CodeIntelligenceApplicationService,
)


class CodeIntelligenceApplicationServiceFactory:
    VERSION = "1.0"

    def create(
        self,
        *,
        capability: CodeIntelligenceCapabilityProtocol,
    ) -> CodeIntelligenceApplicationService:
        if capability is None:
            raise ValueError(
                "code intelligence capability required"
            )

        service = CodeIntelligenceApplicationService(
            capability=capability,
        )

        self._validate(service)
        return service

    @staticmethod
    def _validate(
        service: CodeIntelligenceApplicationService,
    ) -> None:
        for name in (
            "inspect",
            "ready",
            "dump",
        ):
            if not callable(
                getattr(service, name, None)
            ):
                raise TypeError(
                    "code intelligence service must expose "
                    f"{name}()"
                )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "CodeIntelligenceApplicationServiceFactory",
]
