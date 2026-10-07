from __future__ import annotations

from backend.core.execution.code_modification_contract import (
    CodeModificationProviderProtocol,
)


class CodeModificationRuntimeCapabilityProvider:
    """
    Runtime publication boundary for the injected
    Core code-modification provider.
    """

    VERSION = "2.0"

    def __init__(
        self,
        provider: CodeModificationProviderProtocol,
    ) -> None:
        if not isinstance(
            provider,
            CodeModificationProviderProtocol,
        ):
            raise TypeError(
                "provider must implement "
                "CodeModificationProviderProtocol"
            )

        if not provider.ready():
            raise RuntimeError(
                "code modification provider unavailable"
            )

        self.provider = provider
        self.execution_count = 0

    def create(
        self,
    ) -> CodeModificationProviderProtocol:
        if not self.ready():
            raise RuntimeError(
                "code modification provider unavailable"
            )

        self.execution_count += 1
        return self.provider

    def ready(
        self,
    ) -> bool:
        return self.provider.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "provider": type(
                self.provider
            ).__name__,
            "ready": self.ready(),
            "execution_count": self.execution_count,
        }


__all__ = [
    "CodeModificationRuntimeCapabilityProvider",
]
