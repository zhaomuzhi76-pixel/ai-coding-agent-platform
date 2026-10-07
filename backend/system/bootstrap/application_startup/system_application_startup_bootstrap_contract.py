from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class SystemApplicationStartupBootstrapContract(
    Protocol,
):
    """
    Top-level bootstrap boundary over the canonical application
    bootstrap implementation.

    Owns:
        - bootstrap delegation
        - startup resolution
        - readiness projection
        - shutdown delegation

    Does not own:
        - ApplicationStartup construction
        - Runtime construction
        - Runtime Session construction
        - API transport
    """

    def start(self) -> object:
        ...

    def stop(self) -> None:
        ...

    def startup(self) -> object | None:
        ...

    def integration_runtime(self) -> object | None:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...
