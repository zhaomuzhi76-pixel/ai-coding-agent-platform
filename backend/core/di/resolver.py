from __future__ import annotations

from backend.core.contracts.value import (
    CoreValue,
)
from backend.core.di.contracts import (
    DependencyLifetime,
    DependencyResolverProtocol,
)
from backend.core.di.registry import (
    DependencyRegistry,
)
from backend.core.di.scope import (
    DependencyScope,
)
from backend.core.di.value_protocol import (
    DependencyProviderProtocol,
    DependencyValueProtocol,
)


class DependencyResolver(
    DependencyResolverProtocol,
):
    """
    Dependency instance resolution boundary.

    Supports singleton, scoped and transient lifetimes.
    """

    VERSION = "2.1"

    def __init__(
        self,
        registry: DependencyRegistry,
        scope: DependencyScope,
    ) -> None:
        if registry is None:
            raise ValueError(
                "dependency registry required"
            )

        if scope is None:
            raise ValueError(
                "dependency scope required"
            )

        self._registry = registry
        self._scope = scope

        self._singletons: dict[
            str,
            DependencyValueProtocol,
        ] = {}

    def resolve(
        self,
        name: str,
    ) -> DependencyValueProtocol:

        normalized = self._normalize_name(
            name
        )

        definition = self._registry.get(
            normalized
        )

        if (
            definition.lifetime
            is DependencyLifetime.SINGLETON
        ):
            if normalized not in self._singletons:
                self._singletons[normalized] = (
                    self._create(
                        definition.provider
                    )
                )

            return self._singletons[normalized]

        if (
            definition.lifetime
            is DependencyLifetime.SCOPED
        ):
            if not self._scope.contains(normalized):
                self._scope.store(
                    normalized,
                    self._create(
                        definition.provider
                    ),
                )

            return self._scope.get(normalized)

        return self._create(
            definition.provider
        )

    def clear_scope(
        self,
    ) -> None:
        self._scope.clear()

    def reset(
        self,
    ) -> None:
        self._singletons.clear()
        self._scope.clear()

    def ready(
        self,
    ) -> bool:
        return (
            self._registry.ready()
            and self._scope.ready()
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "registry": self._registry.dump(),
            "scope": self._scope.dump(),
            "singleton_count": len(
                self._singletons
            ),
        }

    @staticmethod
    def _create(
        provider: (
            DependencyProviderProtocol
            | DependencyValueProtocol
        ),
    ) -> DependencyValueProtocol:
        if isinstance(
            provider,
            DependencyProviderProtocol,
        ):
            return provider()

        return provider

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
    "DependencyResolver",
]
