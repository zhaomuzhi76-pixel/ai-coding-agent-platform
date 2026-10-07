from __future__ import annotations

from typing import Any

from backend.registry.catalog import (
    RegistryCatalog,
)


class UnifiedRegistryResolver:
    """
    Unified registry resolution boundary.

    Resolution uses the catalog first and therefore does not
    require callers to know which subsystem registry owns an item.
    """

    VERSION = "1.0"

    def __init__(
        self,
        catalog: RegistryCatalog,
    ) -> None:
        if catalog is None:
            raise ValueError(
                "registry catalog required"
            )
        self.catalog = catalog

    def resolve(
        self,
        category: str,
        name: str,
    ) -> Any:
        return self.catalog.get(
            category,
            name,
        ).item

    def record(
        self,
        category: str,
        name: str,
    ):
        return self.catalog.get(
            category,
            name,
        )

    def exists(
        self,
        category: str,
        name: str,
    ) -> bool:
        return self.catalog.exists(
            category,
            name,
        )

    def ready(self) -> bool:
        return self.catalog.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "catalog": self.catalog.dump(),
            "ready": self.ready(),
        }


__all__ = [
    "UnifiedRegistryResolver",
]
