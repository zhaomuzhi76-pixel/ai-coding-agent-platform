from __future__ import annotations

from backend.application.modules.runtime_code_modification_adapter import (
    RuntimeCodeModificationAdapter,
)
from backend.core.execution.code_modification_contract import (
    CodeModificationProviderProtocol,
)


class RuntimeCodeModificationAdapterFactory:
    """
    Sole construction owner for the application modification adapter.
    """

    VERSION = "3.0"

    def create(
        self,
        *,
        provider: CodeModificationProviderProtocol,
    ) -> RuntimeCodeModificationAdapter:
        if not self.ready():
            raise RuntimeError(
                "runtime code modification adapter factory unavailable"
            )

        if not isinstance(
            provider,
            CodeModificationProviderProtocol,
        ):
            raise TypeError(
                "code modification provider contract required"
            )

        adapter = RuntimeCodeModificationAdapter(
            provider
        )

        if not adapter.ready():
            raise RuntimeError(
                "runtime code modification adapter unavailable"
            )

        return adapter

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "RuntimeCodeModificationAdapterFactory",
]
