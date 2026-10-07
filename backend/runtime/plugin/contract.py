from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class RuntimePluginProtocol(
    Protocol,
):
    """
    Runtime plugin extension contract.

    Responsibility:

        - plugin identity
        - plugin registration
        - plugin lifecycle


    Not Responsible:

        - runtime execution
        - business logic
        - persistence
        - scheduling
    """


    name: str

    version: str


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
    "RuntimePluginProtocol",
]
