from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderCapabilityDescriptor:
    """
    Declarative provider capability identity.

    When no explicit implementation method is supplied, the capability
    name is the canonical method name.
    """

    provider: str
    name: str
    version: str = "1.0"
    method: str = ""

    def __post_init__(self) -> None:
        if not self.provider:
            raise ValueError(
                "provider name required"
            )

        if not self.name:
            raise ValueError(
                "capability name required"
            )

        if not self.method:
            object.__setattr__(
                self,
                "method",
                self.name,
            )

    def key(self) -> str:
        return (
            f"{self.provider}.{self.name}"
        )

    def ready(self) -> bool:
        return bool(
            self.provider
            and self.name
            and self.version
            and self.method
        )

    def dump(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "name": self.name,
            "version": self.version,
            "method": self.method,
            "key": self.key(),
            "ready": self.ready(),
        }


__all__ = [
    "ProviderCapabilityDescriptor",
]
