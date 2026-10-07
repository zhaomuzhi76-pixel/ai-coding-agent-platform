from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilityDescriptor:
    """
    Immutable capability metadata.

    Responsibility:
        - capability identity
        - capability description

    Does not own:
        - capability execution
        - registry state
        - lifecycle
    """

    name: str
    description: str

    def ready(self) -> bool:
        return bool(
            isinstance(self.name, str)
            and self.name.strip()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.name,
            "description": self.description,
            "ready": self.ready(),
        }


__all__ = [
    "CapabilityDescriptor",
]
