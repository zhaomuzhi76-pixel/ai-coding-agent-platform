from __future__ import annotations

from dataclasses import dataclass

from backend.core.contracts.value import CoreValue


@dataclass(
    frozen=True,
    slots=True,
)
class ModuleDescriptor:
    """
    Immutable module identity descriptor.

    Owns:
        - module declaration metadata

    Does not own:
        - lifecycle
        - execution
        - dependency resolution
    """

    name: str
    version: str
    category: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError(
                "module name required"
            )

        if not self.version.strip():
            raise ValueError(
                "module version required"
            )

        if not self.category.strip():
            raise ValueError(
                "module category required"
            )

    def dump(self) -> dict[str, CoreValue]:
        return {
            "name": self.name,
            "version": self.version,
            "category": self.category,
        }


__all__ = [
    "ModuleDescriptor",
]
