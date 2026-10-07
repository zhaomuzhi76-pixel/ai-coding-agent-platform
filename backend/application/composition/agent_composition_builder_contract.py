from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.application.composition.agent_runtime_port import (
    ApplicationAgentRuntimePortProtocol,
)
@runtime_checkable
class ApplicationAgentCompositionBuilderProtocol(Protocol):
    def create(
        self,
        *,

        runtime: ApplicationAgentRuntimePortProtocol,
        runtime_execution_session_flow: object,
        context_factory: object,
    ) -> dict[str, object]:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


__all__ = [
    "ApplicationAgentCompositionBuilderProtocol",
]
