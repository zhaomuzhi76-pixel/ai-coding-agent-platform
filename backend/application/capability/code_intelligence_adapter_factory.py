from __future__ import annotations

from backend.application.capability.code_intelligence_adapter import (
    CodeIntelligenceApplicationCapabilityAdapter,
)
from backend.application.code_intelligence.service import (
    CodeIntelligenceApplicationService,
)


class CodeIntelligenceApplicationCapabilityAdapterFactory:
    """
    Sole construction owner for
    CodeIntelligenceApplicationCapabilityAdapter.
    """

    VERSION = "1.0"

    def create(
        self,
        *,
        service: CodeIntelligenceApplicationService,
    ) -> CodeIntelligenceApplicationCapabilityAdapter:
        if not self.ready():
            raise RuntimeError(
                "code intelligence adapter factory unavailable"
            )

        if not isinstance(
            service,
            CodeIntelligenceApplicationService,
        ):
            raise TypeError(
                "service must CodeIntelligenceApplicationService"
            )

        adapter = (
            CodeIntelligenceApplicationCapabilityAdapter(
                service
            )
        )

        self._validate(adapter)
        return adapter

    @staticmethod
    def _validate(
        adapter: CodeIntelligenceApplicationCapabilityAdapter,
    ) -> None:
        for name in (
            "initialize",
            "shutdown",
            "ready",
            "dump",
        ):
            if not callable(
                getattr(adapter, name, None)
            ):
                raise TypeError(
                    "code intelligence adapter must expose "
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
    "CodeIntelligenceApplicationCapabilityAdapterFactory",
]
