from __future__ import annotations

from collections.abc import Callable
from typing import Any

from backend.registry.contracts import RegistryTargetProtocol


class RegistryBinding:
    """
    Adapt one subsystem registry to the unified registry boundary.
    """

    VERSION = "1.1"

    def __init__(
        self,
        category: str,
        registry: RegistryTargetProtocol,
        register: Callable[[Any], None],
        resolve: Callable[[str], Any] | None = None,
    ) -> None:
        if not isinstance(category, str) or not category.strip():
            raise ValueError("registry category required")

        if not isinstance(
            registry,
            RegistryTargetProtocol,
        ):
            raise TypeError(
                "registry must implement RegistryTargetProtocol"
            )

        if not callable(register):
            raise TypeError("register callback required")

        if resolve is not None and not callable(resolve):
            raise TypeError("resolve callback must be callable")

        self.category = category.strip()
        self.registry = registry
        self._register = register
        self._resolve = resolve

    def register(self, item: Any) -> None:
        self._register(item)

    def resolve(self, name: str) -> Any:
        if self._resolve is None:
            raise NotImplementedError(
                f"resolve unavailable: {self.category}"
            )
        return self._resolve(name)

    def ready(self) -> bool:
        return self.registry.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "category": self.category,
            "registry": type(self.registry).__name__,
            "ready": self.ready(),
        }


__all__ = [
    "RegistryBinding",
]
