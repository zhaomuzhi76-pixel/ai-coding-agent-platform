from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class RuntimeExecutionSessionBindableFlowProtocol(
    Protocol,
):
    """
    Minimal flow capability required by the binding layer.

    Binding depends only on this lower-level capability surface.
    """

    async def execute(
        self,
        *,
        request: object,
        context: object,
        stream_callback: object | None = None,
    ) -> list[object]:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, object]:
        ...


@runtime_checkable
class RuntimeExecutionSessionBindingContract(
    Protocol,
):
    """
    Application binding contract for a runtime session flow.

    Owns:
        - context registration
        - context resolution

    Does not own:
        - flow construction
        - composition
        - lifecycle
        - execution
    """

    KEY = "runtime_execution_session_flow"

    def bind(
        self,
        context: dict[str, object],
    ) -> RuntimeExecutionSessionBindableFlowProtocol:
        ...

    def resolve(
        self,
        context: dict[str, object],
    ) -> RuntimeExecutionSessionBindableFlowProtocol:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, object]:
        ...


__all__ = [
    "RuntimeExecutionSessionBindableFlowProtocol",
    "RuntimeExecutionSessionBindingContract",
]
