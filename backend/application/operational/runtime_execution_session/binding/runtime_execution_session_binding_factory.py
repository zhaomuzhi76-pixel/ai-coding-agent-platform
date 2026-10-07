from __future__ import annotations

from backend.application.operational.runtime_execution_session.binding.runtime_execution_session_binding import (
    RuntimeExecutionSessionBinding,
)
from backend.application.operational.runtime_execution_session.binding.runtime_execution_session_binding_contract import (
    RuntimeExecutionSessionBindableFlowProtocol,
)


class RuntimeExecutionSessionBindingFactory:
    """
    Factory for the lower-level runtime session binding.

    Construction of the flow remains outside this layer.
    """

    VERSION = "2.0"

    def create(
        self,
        flow: RuntimeExecutionSessionBindableFlowProtocol,
    ) -> RuntimeExecutionSessionBinding:
        if not isinstance(
            flow,
            RuntimeExecutionSessionBindableFlowProtocol,
        ):
            raise TypeError(
                "flow must implement "
                "RuntimeExecutionSessionBindableFlowProtocol"
            )

        binding = RuntimeExecutionSessionBinding(flow)

        if not binding.ready():
            raise RuntimeError(
                "runtime session binding unavailable"
            )

        return binding

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "RuntimeExecutionSessionBindingFactory",
]
