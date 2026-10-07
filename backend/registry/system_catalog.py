from __future__ import annotations

from typing import Any

from backend.registry.binding import (
    RegistryBinding,
)
from backend.registry.catalog import (
    RegistryCatalog,
    RegistryRecord,
)


class SystemRegistry:
    """
    System-wide registry integration boundary.

    Responsibility:
        - own subsystem registry bindings
        - maintain unified metadata catalog
        - resolve registered subsystem objects

    Not Responsible:
        - subsystem construction
        - subsystem discovery
        - application composition
        - bootstrap lifecycle
    """

    VERSION = "1.1"

    def __init__(
        self,
        catalog: RegistryCatalog | None = None,
    ) -> None:
        self.catalog = (
            catalog
            or RegistryCatalog()
        )
        self._bindings: dict[
            str,
            RegistryBinding,
        ] = {}

    def bind(
        self,
        binding: RegistryBinding,
    ) -> None:
        if binding is None:
            raise ValueError(
                "registry binding required"
            )

        if binding.category in self._bindings:
            raise ValueError(
                "registry binding already exists: "
                f"{binding.category}"
            )

        self._bindings[
            binding.category
        ] = binding

    def register(
        self,
        *,
        category: str,
        item: Any,
        name: str,
        version: str = "1.0",
    ) -> RegistryRecord:
        binding = self._binding(category)

        binding.register(item)

        record = RegistryRecord(
            category=category,
            name=name,
            version=version,
            item=item,
        )

        self.catalog.add(record)
        return record

    def binding(
        self,
        category: str,
    ) -> RegistryBinding:
        return self._binding(category)

    def resolve(
        self,
        category: str,
        name: str,
    ) -> Any:
        if self.catalog.exists(
            category,
            name,
        ):
            return self.catalog.get(
                category,
                name,
            ).item

        return self._binding(
            category
        ).resolve(name)

    def categories(self) -> tuple[str, ...]:
        return tuple(self._bindings)

    def ready(self) -> bool:
        return (
            all(
                binding.ready()
                for binding
                in self._bindings.values()
            )
            and self.catalog.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "categories": self.categories(),
            "bindings": {
                category: binding.dump()
                for category, binding
                in self._bindings.items()
            },
            "catalog": self.catalog.dump(),
            "ready": self.ready(),
        }

    def _binding(
        self,
        category: str,
    ) -> RegistryBinding:
        try:
            return self._bindings[category]
        except KeyError as error:
            raise LookupError(
                f"registry binding not found: {category}"
            ) from error


__all__ = [
    "SystemRegistry",
]
