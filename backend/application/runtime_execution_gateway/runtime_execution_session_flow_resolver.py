from __future__ import annotations

from backend.application.operational.runtime_execution_session.runtime_execution_session_flow_contract import (
    RuntimeExecutionSessionFlowContract,
)


class RuntimeExecutionSessionFlowResolver:
    """
    Late-binding resolver for the startup-created runtime session flow.

    Owns:
        - startup-time flow binding
        - request-time flow resolution

    Does not own:
        - flow construction
        - lifecycle orchestration
        - runtime execution
        - request context construction
    """

    VERSION = "1.0"

    def __init__(self) -> None:
        self._flow: RuntimeExecutionSessionFlowContract | None = None
        self.bind_count = 0
        self.resolve_count = 0

    def bind(
        self,
        flow: RuntimeExecutionSessionFlowContract,
    ) -> None:
        if not isinstance(
            flow,
            RuntimeExecutionSessionFlowContract,
        ):
            raise TypeError(
                "flow must implement "
                "RuntimeExecutionSessionFlowContract"
            )

        if not flow.ready():
            raise RuntimeError(
                "runtime execution session flow not ready"
            )

        if (
            self._flow is not None
            and self._flow is not flow
        ):
            raise RuntimeError(
                "runtime execution session flow already bound"
            )

        self._flow = flow
        self.bind_count += 1

    def resolve(
        self,
    ) -> RuntimeExecutionSessionFlowContract:
        flow = self._flow

        if flow is None:
            raise RuntimeError(
                "runtime execution session flow not bound"
            )

        if not flow.ready():
            raise RuntimeError(
                "runtime execution session flow not ready"
            )

        self.resolve_count += 1
        return flow

    def bound(self) -> bool:
        return self._flow is not None

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "bound": self.bound(),
            "bind_count": self.bind_count,
            "resolve_count": self.resolve_count,
            "flow": (
                type(self._flow).__name__
                if self._flow is not None
                else None
            ),
        }


__all__ = [
    "RuntimeExecutionSessionFlowResolver",
]
