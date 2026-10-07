from __future__ import annotations

from typing import Protocol, runtime_checkable

from fastapi import FastAPI


@runtime_checkable
class FastAPIHTTPRuntimeEntryContract(
    Protocol,
):
    """
    Canonical HTTP runtime entry boundary.

    Owns:
        - HTTP runtime registration lifecycle
        - registration readiness
        - registration cleanup

    Does not own:
        - submission execution
        - runtime execution
        - application construction
        - system bootstrap
        - FastAPI application construction
    """

    def start(
        self,
        *,
        application: FastAPI,
        startup: object,
    ) -> None:
        ...

    def stop(
        self,
        application: FastAPI,
    ) -> None:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def registered(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, object]:
        ...


__all__ = [
    "FastAPIHTTPRuntimeEntryContract",
]
