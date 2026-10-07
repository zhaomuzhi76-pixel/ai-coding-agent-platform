from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from backend.core.di.lifetime import (
    DependencyLifetime,
)

from backend.core.di.value_protocol import (
    DependencyProviderProtocol,
    DependencyValueProtocol,
)


DependencyT = TypeVar(
    "DependencyT",
    bound=DependencyValueProtocol,
)


@runtime_checkable
class DependencyRegistryProtocol(
    Protocol,
):

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
        ...


    def exists(
        self,
        name: str,
    ) -> bool:
        ...


    def get(
        self,
        name: str,
    ):
        ...


@runtime_checkable
class DependencyResolverProtocol(
    Protocol,
):

    def resolve(
        self,
        name: str,
    ) -> DependencyValueProtocol:
        ...


    def ready(
        self,
    ) -> bool:
        ...


__all__ = [
    "DependencyLifetime",
    "DependencyRegistryProtocol",
    "DependencyResolverProtocol",
]
