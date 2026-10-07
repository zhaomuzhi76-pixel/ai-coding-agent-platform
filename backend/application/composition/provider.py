from __future__ import annotations

from backend.application.provider_gateway.contracts import (
    ApplicationProviderRuntimeProtocol,
)
from backend.application.provider_gateway.gateway import (
    ApplicationProviderGateway,
)


class ApplicationProviderComposition:
    """
    Application provider exposure boundary.

    Owns:
        - injected provider runtime admission
        - application gateway exposure

    Does not own:
        - provider configuration
        - provider registration
        - provider construction
        - provider execution
    """

    VERSION = "4.0"

    def __init__(
        self,
        *,
        runtime: ApplicationProviderRuntimeProtocol,
    ) -> None:
        if not isinstance(
            runtime,
            ApplicationProviderRuntimeProtocol,
        ):
            raise TypeError(
                "provider runtime contract required"
            )

        if not runtime.ready():
            raise RuntimeError(
                "provider runtime unavailable"
            )

        self.runtime = runtime

    def create(
        self,
    ) -> ApplicationProviderGateway:
        gateway = ApplicationProviderGateway(
            self.runtime
        )

        if not gateway.ready():
            raise RuntimeError(
                "application provider gateway unavailable"
            )

        return gateway

    def ready(
        self,
    ) -> bool:
        return bool(
            isinstance(
                self.runtime,
                ApplicationProviderRuntimeProtocol,
            )
            and self.runtime.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "runtime": type(
                self.runtime
            ).__name__,
        }


__all__ = [
    "ApplicationProviderComposition",
]
