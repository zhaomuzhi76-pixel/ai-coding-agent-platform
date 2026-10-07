from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class DependencyValueProtocol(
    Protocol,
):
    """
    Structural boundary for values managed by DI.

    The protocol is intentionally capability-free.
    It represents an opaque dependency instance without
    widening the public contract type surface.
    """


@runtime_checkable
class DependencyProviderProtocol(
    Protocol,
):
    """
    Dependency construction capability.
    """

    def __call__(
        self,
    ) -> DependencyValueProtocol:
        ...


__all__ = [
    "DependencyProviderProtocol",
    "DependencyValueProtocol",
]
