from __future__ import annotations

from backend.application.composition.provider import (
    ApplicationProviderComposition,
)
from backend.application.provider_gateway.contracts import (
    ApplicationProviderRuntimeProtocol,
)


class ApplicationProviderCompositionFactory:
    """
    Sole construction owner for ApplicationProviderComposition.

    Provider construction is intentionally external and injected.
    """

    VERSION = "2.0"

    def create(
        self,
        *,
        runtime: ApplicationProviderRuntimeProtocol,
    ) -> ApplicationProviderComposition:
        if not isinstance(
            runtime,
            ApplicationProviderRuntimeProtocol,
        ):
            raise TypeError(
                "provider runtime contract required"
            )

        composition = ApplicationProviderComposition(
            runtime=runtime
        )

        if not composition.ready():
            raise RuntimeError(
                "application provider composition unavailable"
            )

        return composition

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
    "ApplicationProviderCompositionFactory",
]
