from __future__ import annotations

from typing import Any

from backend.api.framework.contracts import (
    APITransportProtocol,
)


class BaseAPITransport(
    APITransportProtocol,
):
    """
    Generic API transport boundary.

    Concrete transports implement handle().
    """

    VERSION = "2.0"
    NAME = "base"
    CATEGORY = "generic"

    def __init__(self) -> None:
        self.initialized = False

    @property
    def name(self) -> str:
        return self.NAME

    @property
    def version(self) -> str:
        return self.VERSION

    async def handle(
        self,
        request: Any,
    ) -> Any:
        raise NotImplementedError(
            "transport handle() must be implemented"
        )

    def initialize(self) -> None:
        self.initialized = True

    def shutdown(self) -> None:
        self.initialized = False

    def ready(self) -> bool:
        return self.initialized

    def dump(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "category": self.CATEGORY,
            "initialized": self.initialized,
            "ready": self.ready(),
        }


__all__ = [
    "BaseAPITransport",
]
