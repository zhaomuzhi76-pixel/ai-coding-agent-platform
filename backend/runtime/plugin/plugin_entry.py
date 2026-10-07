from __future__ import annotations


from typing import Protocol, runtime_checkable


from backend.runtime.plugin.capability import (
    RuntimeCapability,
)


@runtime_checkable
class RuntimePluginEntryProtocol(
    Protocol,
):
    """
    Runtime plugin entry contract.

    Responsibility:
        - expose plugin identity
        - provide capabilities
        - register plugin resources

    Not Responsible:
        - business execution
        - runtime scheduling
        - persistence
    """


    name: str

    version: str


    def capabilities(
        self,
    ) -> list[RuntimeCapability]:
        ...


    def register(
        self,
        registry,
    ) -> None:
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
    "RuntimePluginEntryProtocol",
]
