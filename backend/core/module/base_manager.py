from __future__ import annotations

from backend.core.contracts.value import CoreValue

from typing import Final

from backend.core.module.component import BaseComponent


class BaseManager(BaseComponent):
    """
    Canonical manager role foundation.

    Owns manager identity and manager capability declaration.
    It does not own persistence, DI, lifecycle or business rules.
    """

    VERSION: Final = "8.0"
    COMPONENT_TYPE: Final = "manager"
    CAPABILITIES: Final[tuple[str, ...]] = ("manage",)

    def __init__(
        self,
        name: str = "manager",
    ) -> None:
        super().__init__(
            name=name,
            component_type=self.COMPONENT_TYPE,
        )

    def ready(self) -> bool:
        return super().ready()

    def dump(self) -> dict[str, CoreValue]:
        return {
            **super().dump(),
            "manager": {
                "ready": self.ready(),
            },
        }


__all__ = [
    "BaseManager",
]
