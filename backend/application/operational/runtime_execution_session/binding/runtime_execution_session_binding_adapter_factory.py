from __future__ import annotations

from backend.application.operational.runtime_execution_session.binding.runtime_execution_session_binding_adapter import (
    RuntimeExecutionSessionBindingAdapter,
)


class RuntimeExecutionSessionBindingAdapterFactory:
    """
    Factory for the provider-to-binding adapter.

    Provider construction remains outside this layer.
    """

    VERSION = "2.0"

    def create(
        self,
        *,
        provider: object,
    ) -> RuntimeExecutionSessionBindingAdapter:
        adapter = RuntimeExecutionSessionBindingAdapter(
            provider=provider,
        )

        if not adapter.ready():
            raise RuntimeError(
                "runtime binding adapter unavailable"
            )

        return adapter

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "RuntimeExecutionSessionBindingAdapterFactory",
]
