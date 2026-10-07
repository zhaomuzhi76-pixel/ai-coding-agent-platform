from __future__ import annotations

from backend.application.composition.agent_runtime_port import (
    ApplicationAgentRuntimePortProtocol,
)
from backend.core.contracts.value import CoreValue


class ApplicationAgentCompositionBuilderSupport:
    VERSION = "3.0"

    def validate_inputs(self, *, runtime: ApplicationAgentRuntimePortProtocol) -> None:
        if not isinstance(runtime, ApplicationAgentRuntimePortProtocol):
            raise TypeError('runtime must implement ApplicationAgentRuntimePortProtocol')
        if not runtime.ready():
            raise RuntimeError('runtime component provider unavailable')

    @staticmethod
    def require_ready(
        value: object,
        label: str,
    ) -> None:
        if value is None:
            raise RuntimeError(f"{label} unavailable")

        ready = getattr(value, "ready", None)

        if not callable(ready):
            raise TypeError(f"{label} must expose ready()")

        if not ready():
            raise RuntimeError(f"{label} unavailable")

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, CoreValue]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationAgentCompositionBuilderSupport",
]
