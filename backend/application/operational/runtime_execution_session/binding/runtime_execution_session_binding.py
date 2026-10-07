from __future__ import annotations

from backend.application.operational.runtime_execution_session.binding.runtime_execution_session_binding_contract import (
    RuntimeExecutionSessionBindableFlowProtocol,
    RuntimeExecutionSessionBindingContract,
)


class RuntimeExecutionSessionBinding(
    RuntimeExecutionSessionBindingContract,
):
    """
    Lowest-level runtime session flow context binding.

    Owns only:
        - context registration
        - context resolution
    """

    VERSION = "2.0"

    KEY = "runtime_execution_session_flow"

    def __init__(
        self,
        flow: RuntimeExecutionSessionBindableFlowProtocol,
    ) -> None:
        if not isinstance(
            flow,
            RuntimeExecutionSessionBindableFlowProtocol,
        ):
            raise TypeError(
                "flow must implement "
                "RuntimeExecutionSessionBindableFlowProtocol"
            )

        if not flow.ready():
            raise RuntimeError(
                "runtime session flow not ready"
            )

        self.flow = flow
        self.bind_count = 0
        self.resolve_count = 0

    def bind(
        self,
        context: dict[str, object],
    ) -> RuntimeExecutionSessionBindableFlowProtocol:
        self._validate_context(context)

        context[self.KEY] = self.flow
        self.bind_count += 1

        return self.flow

    def resolve(
        self,
        context: dict[str, object],
    ) -> RuntimeExecutionSessionBindableFlowProtocol:
        self._validate_context(context)

        value = context.get(self.KEY)

        if not isinstance(
            value,
            RuntimeExecutionSessionBindableFlowProtocol,
        ):
            raise RuntimeError(
                "runtime execution session flow not bound"
            )

        if not value.ready():
            raise RuntimeError(
                "bound runtime session flow not ready"
            )

        self.resolve_count += 1
        return value

    def ready(self) -> bool:
        return self.flow.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "key": self.KEY,
            "bind_count": self.bind_count,
            "resolve_count": self.resolve_count,
            "flow": type(self.flow).__name__,
        }

    @staticmethod
    def _validate_context(
        context: dict[str, object],
    ) -> None:
        if not isinstance(context, dict):
            raise TypeError(
                "application context must dict"
            )


__all__ = [
    "RuntimeExecutionSessionBinding",
]
