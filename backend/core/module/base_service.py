from __future__ import annotations

from backend.core.contracts.value import CoreValue

from typing import Final

from backend.core.module.component import BaseComponent


class BaseService(BaseComponent):
    """
    Canonical service role foundation.

    Owns service identity and execution boundary.
    Business implementation remains in concrete services.
    """

    VERSION: Final = "7.0"
    COMPONENT_TYPE: Final = "service"
    CAPABILITIES: Final[tuple[str, ...]] = ("execute",)

    def __init__(
        self,
        name: str = "service",
    ) -> None:
        super().__init__(
            name=name,
            component_type=self.COMPONENT_TYPE,
        )

    def execute(self, request: CoreValue) -> CoreValue:
        raise NotImplementedError(
            "service must implement execute()"
        )

    def ready(self) -> bool:
        return super().ready()

    def dump(self) -> dict[str, CoreValue]:
        return {
            **super().dump(),
            "service": {
                "ready": self.ready(),
            },
        }


__all__ = [
    "BaseService",
]
