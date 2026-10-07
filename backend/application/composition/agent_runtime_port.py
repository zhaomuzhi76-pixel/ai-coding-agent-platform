from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.application.runtime_execution_gateway.runtime_execution_result_port import (
    ApplicationExecutionResultFactoryProtocol,
)


@runtime_checkable
class ApplicationAgentRuntimePortProtocol(Protocol):
    """
    Narrow Application-to-Runtime composition port.

    Agent composition consumes only:
        - runtime readiness
        - runtime result-factory creation
    """

    def ready(self) -> bool:
        ...

    def create_result_factory(
        self,
    ) -> ApplicationExecutionResultFactoryProtocol:
        ...


__all__ = [
    "ApplicationAgentRuntimePortProtocol",
]
