from __future__ import annotations

from backend.core.contracts.value import CoreValue

from backend.core.context.registry_item_protocol import (
    ContextRegistryItemProtocol,
)


class ContextRegistry:
    """
    Runtime context registry.

    Responsibility:

        - register context references
        - retrieve context references
        - remove context references
        - expose registry state

    Not Responsible:

        - context creation
        - execution
        - persistence
        - lifecycle
    """

    VERSION = "6.0"

    RESPONSIBILITY = (
        "runtime_context_registry",
    )

    def __init__(
        self,
    ) -> None:

        self._contexts: dict[
            str,
            ContextRegistryItemProtocol,
        ] = {}

    def register(
        self,
        context_id: str,
        context: ContextRegistryItemProtocol,
    ) -> None:

        if not isinstance(
            context_id,
            str,
        ) or not context_id.strip():

            raise ValueError(
                "context_id required"
            )

        if not isinstance(
            context,
            ContextRegistryItemProtocol,
        ):
            raise TypeError(
                "context must implement ContextRegistryItemProtocol"
            )

        context_id = context_id.strip()

        if context_id in self._contexts:
            raise ValueError(
                f"context already registered: {context_id}"
            )

        self._contexts[
            context_id
        ] = context

    def get(
        self,
        context_id: str,
    ) -> ContextRegistryItemProtocol | None:

        return self._contexts.get(
            context_id
        )

    def remove(
        self,
        context_id: str,
    ) -> None:

        self._contexts.pop(
            context_id,
            None,
        )

    def list_contexts(
        self,
    ) -> tuple[str, ...]:

        return tuple(
            self._contexts.keys()
        )

    def count(
        self,
    ) -> int:

        return len(
            self._contexts
        )

    def clear(
        self,
    ) -> None:

        self._contexts.clear()

    def ready(
        self,
    ) -> bool:

        return isinstance(
            self._contexts,
            dict,
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:

        return {
            "name": "ContextRegistry",
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "contexts": self.list_contexts(),
            "count": self.count(),
        }


__all__ = [
    "ContextRegistry",
]
