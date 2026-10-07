from __future__ import annotations

from typing import Final

from backend.core.contracts.value import CoreValue
from backend.core.module.component import BaseComponent


class BaseProvider(
    BaseComponent,
):
    """
    Canonical framework provider foundation.

    Owns:
        - external capability boundary
        - provider identity

    Does not own:
        - business workflow
        - routing
        - selection
        - retry policy
        - persistence
    """

    VERSION: Final = "8.0"

    COMPONENT_TYPE: Final = "provider"

    CATEGORY: Final = "provider"

    CAPABILITIES: Final[tuple[str, ...]] = (
        "provide",
    )

    def __init__(
        self,
        name: str = "provider",
    ) -> None:

        super().__init__(
            name=name,
            component_type=self.COMPONENT_TYPE,
        )

    @property
    def version(
        self,
    ) -> str:
        return self.VERSION

    @property
    def category(
        self,
    ) -> str:
        return self.CATEGORY

    def provide(
        self,
        request: CoreValue,
    ) -> CoreValue:
        raise NotImplementedError(
            "provider must implement provide()"
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:

        return {
            **super().dump(),
            "provider": {
                "version": self.version,
                "category": self.category,
            },
        }


__all__ = [
    "BaseProvider",
]
