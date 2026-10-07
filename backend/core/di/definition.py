from __future__ import annotations

from dataclasses import dataclass

from backend.core.di.lifetime import (
    DependencyLifetime,
)

from backend.core.di.value_protocol import (
    DependencyProviderProtocol,
    DependencyValueProtocol,
)


@dataclass(frozen=True)
class DependencyDefinition:
    """
    Immutable dependency definition.

    Owns:
        - dependency identity
        - provider reference
        - lifetime policy

    Does not own:
        - registration
        - resolution
        - instance storage
    """

    name: str

    provider: (
        DependencyProviderProtocol
        | DependencyValueProtocol
    )

    lifetime: DependencyLifetime

    VERSION = "1.0"

    def __post_init__(
        self,
    ) -> None:

        if not isinstance(
            self.name,
            str,
        ):
            raise TypeError(
                "dependency name must str"
            )

        normalized = self.name.strip()

        if not normalized:
            raise ValueError(
                "dependency name required"
            )

        object.__setattr__(
            self,
            "name",
            normalized,
        )

        if self.provider is None:
            raise ValueError(
                "dependency provider required"
            )

        if not isinstance(
            self.lifetime,
            DependencyLifetime,
        ):
            raise TypeError(
                "invalid dependency lifetime"
            )

    def ready(
        self,
    ) -> bool:

        return bool(
            self.name
            and self.provider is not None
            and isinstance(
                self.lifetime,
                DependencyLifetime,
            )
        )

    def dump(
        self,
    ) -> dict[str, str | bool]:

        return {
            "name": self.name,
            "lifetime": self.lifetime.value,
            "provider": type(
                self.provider
            ).__name__,
            "ready": self.ready(),
        }


__all__ = [
    "DependencyDefinition",
]
