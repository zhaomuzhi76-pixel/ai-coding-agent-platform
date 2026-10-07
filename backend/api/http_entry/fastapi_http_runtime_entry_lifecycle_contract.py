from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class FastAPIHTTPRuntimeEntryLifecycleContract(
    Protocol,
):
    """
    Minimal lifecycle contract consumed by the HTTP entry.

    Owns only:
        - router registration
        - router cleanup
        - registration state
        - readiness projection
        - diagnostics

    Concrete routing implementation remains outside this contract.
    """

    def register(
        self,
        app: object,
        startup: object,
    ) -> None:
        ...

    def unregister(
        self,
        app: object,
    ) -> None:
        ...

    def registered(
        self,
    ) -> bool:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, object]:
        ...


__all__ = [
    "FastAPIHTTPRuntimeEntryLifecycleContract",
]
