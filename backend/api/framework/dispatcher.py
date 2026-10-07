from __future__ import annotations

from typing import Any

from backend.api.framework.registry import (
    APITransportRegistry,
)


class APIDispatcher:
    """
    Generic API dispatch boundary.

    Resolves a transport and delegates request handling.
    """

    VERSION = "2.0"

    def __init__(
        self,
        registry: APITransportRegistry,
    ) -> None:
        if registry is None:
            raise ValueError(
                "API transport registry required"
            )

        self.registry = registry
        self.request_count = 0
        self.failure_count = 0

    async def dispatch(
        self,
        transport_name: str,
        request: Any,
    ) -> Any:
        if not transport_name:
            raise ValueError(
                "transport name required"
            )

        transport = self.registry.resolve(
            transport_name
        )

        if not transport.ready():
            raise RuntimeError(
                f"API transport unavailable: "
                f"{transport_name}"
            )

        try:
            result = await transport.handle(
                request
            )
            self.request_count += 1
            return result

        except Exception:
            self.failure_count += 1
            raise

    def ready(self) -> bool:
        return self.registry.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "request_count": self.request_count,
            "failure_count": self.failure_count,
            "registry": self.registry.dump(),
            "ready": self.ready(),
        }


__all__ = [
    "APIDispatcher",
]
