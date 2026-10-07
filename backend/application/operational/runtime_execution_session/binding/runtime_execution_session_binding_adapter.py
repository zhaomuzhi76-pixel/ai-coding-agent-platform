from __future__ import annotations

from backend.application.operational.runtime_execution_session.binding.runtime_execution_session_binding_contract import (
    RuntimeExecutionSessionBindableFlowProtocol,
)


class RuntimeExecutionSessionBindingAdapter:
    """
    Generic provider-to-binding adapter.

    The provider is intentionally structural so this lower layer
    does not depend on RuntimeExecutionSessionComposition.
    """

    VERSION = "2.0"

    def __init__(
        self,
        *,
        provider: object,
    ) -> None:
        if provider is None:
            raise ValueError(
                "binding provider required"
            )

        create = getattr(provider, "create", None)

        if not callable(create):
            raise TypeError(
                "binding provider must expose create()"
            )

        self.provider = provider
        self.resolve_count = 0

    def resolve(
        self,
    ) -> RuntimeExecutionSessionBindableFlowProtocol:
        flow = self.provider.create()

        if not isinstance(
            flow,
            RuntimeExecutionSessionBindableFlowProtocol,
        ):
            raise TypeError(
                "provider must create bindable runtime flow"
            )

        if not flow.ready():
            raise RuntimeError(
                "runtime execution session flow unavailable"
            )

        self.resolve_count += 1
        return flow

    def ready(self) -> bool:
        return callable(
            getattr(
                self.provider,
                "create",
                None,
            )
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "resolve_count": self.resolve_count,
            "provider": type(self.provider).__name__,
        }


__all__ = [
    "RuntimeExecutionSessionBindingAdapter",
]
