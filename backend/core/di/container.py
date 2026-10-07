from __future__ import annotations

from backend.core.contracts.value import (
    CoreValue,
)
from backend.core.di.lifetime import (
    DependencyLifetime,
)
from backend.core.di.registry import (
    DependencyRegistry,
)
from backend.core.di.resolver import (
    DependencyResolver,
)
from backend.core.di.scope import (
    DependencyScope,
)
from backend.core.di.value_protocol import (
    DependencyProviderProtocol,
    DependencyValueProtocol,
)


class Container:
    """
    Industrial dependency injection container.

    Owns registration, resolution and scope coordination.
    """

    VERSION = "6.2"

    RESPONSIBILITY = (
        "dependency_registration",
        "dependency_resolution",
        "scope_management",
    )

    def __init__(
        self,
        scope_name: str = "default",
    ) -> None:
        self._registry = DependencyRegistry()

        self._scope = DependencyScope(
            scope_name
        )

        self._resolver = DependencyResolver(
            self._registry,
            self._scope,
        )

        self._frozen = False

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

        if self._frozen:
            raise RuntimeError(
                "container frozen"
            )

        self._registry.register(
            name,
            provider,
            lifetime,
        )

    def resolve(
        self,
        name: str,
    ) -> DependencyValueProtocol:
        return self._resolver.resolve(name)

    def contains(
        self,
        name: str,
    ) -> bool:
        return self._registry.exists(name)

    def clear_scope(
        self,
    ) -> None:
        self._resolver.clear_scope()

    def reset(
        self,
    ) -> None:
        self._resolver.reset()

    def child_scope(
        self,
        name: str,
    ) -> "Container":
        child = Container(name)

        for definition in (
            self._registry.definitions()
        ):
            child.register(
                definition.name,
                definition.provider,
                definition.lifetime,
            )

        return child

    def freeze(
        self,
    ) -> None:
        self._frozen = True


    def ready(
        self,
    ) -> bool:
        return (
            self._resolver.ready()
            and isinstance(
                self._frozen,
                bool,
            )
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "frozen": self._frozen,
            "ready": self.ready(),
            "registry": self._registry.dump(),
            "resolver": self._resolver.dump(),
        }


__all__ = [
    "Container",
]
