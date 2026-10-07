from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApplicationCapabilityDescriptor:
    """
    Declarative application capability identity.
    """

    name: str
    version: str = "1.0"
    category: str = "application"
    capabilities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError(
                "capability name required"
            )

        if not self.version:
            raise ValueError(
                "capability version required"
            )

        if not self.category:
            raise ValueError(
                "capability category required"
            )

        if len(self.capabilities) != len(
            set(self.capabilities)
        ):
            raise ValueError(
                "capabilities must be unique"
            )

    def key(self) -> str:
        return (
            f"{self.category}."
            f"{self.name}:"
            f"{self.version}"
        )

    def ready(self) -> bool:
        return bool(
            self.name
            and self.version
            and self.category
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "category": self.category,
            "capabilities": self.capabilities,
            "key": self.key(),
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationCapabilityDescriptor",
]
