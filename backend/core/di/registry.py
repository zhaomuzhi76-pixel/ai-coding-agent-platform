from __future__ import annotations

from backend.core.di.lifetime import (
    DependencyLifetime,
)

from backend.core.di.contracts import (
    DependencyRegistryProtocol,
)

from backend.core.di.definition import (
    DependencyDefinition,
)

from backend.core.di.value_protocol import (
    DependencyProviderProtocol,
    DependencyValueProtocol,
)


class DependencyRegistry(
    DependencyRegistryProtocol,
):
    """
    Dependency definition registry.

    Owns:
        - dependency definition storage
        - registration lookup

    Does not own:
        - instance creation
        - lifecycle execution
        - scope management
    """

    VERSION = "3.0"

    def __init__(
        self,
    ) -> None:

        self._definitions: dict[
            str,
            DependencyDefinition,
        ] = {}

    def register(
        self,
        name: str,
        provider: (
            DependencyProviderProtocol
            | DependencyValueProtocol
        ),
        lifetime: DependencyLifetime = (
            DependencyLifetime.SINGLETON
        ),
    ) -> None:

        normalized = self._normalize_name(
            name
        )

        if self.exists(
            normalized,
        ):
            raise ValueError(
                f"dependency exists: {normalized}"
            )

        self._definitions[
            normalized
        ] = DependencyDefinition(
            name=normalized,
            provider=provider,
            lifetime=lifetime,
        )

    def exists(
        self,
        name: str,
    ) -> bool:

        return (
            self._normalize_name(name)
            in self._definitions
        )

    def get(
        self,
        name: str,
    ) -> DependencyDefinition:

        normalized = self._normalize_name(
            name
        )

        try:
            return self._definitions[
                normalized
            ]

        except KeyError as error:
            raise KeyError(
                f"dependency missing: {normalized}"
            ) from error

    def names(
        self,
    ) -> tuple[str, ...]:

        return tuple(
            self._definitions
        )

    def definitions(
        self,
    ) -> tuple[
        DependencyDefinition,
        ...,
    ]:

        return tuple(
            self._definitions.values()
        )

    def ready(
        self,
    ) -> bool:

        return all(
            definition.ready()
            for definition
            in self._definitions.values()
        )

    def dump(
        self,
    ) -> dict:

        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "count": len(
                self._definitions
            ),
            "dependencies": {
                item.name: item.lifetime.value
                for item
                in self._definitions.values()
            },
            "ready": self.ready(),
        }

    @staticmethod
    def _normalize_name(
        name: str,
    ) -> str:

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "dependency name must str"
            )

        normalized = name.strip()

        if not normalized:
            raise ValueError(
                "dependency name required"
            )

        return normalized


__all__ = [
    "DependencyRegistry",
]
