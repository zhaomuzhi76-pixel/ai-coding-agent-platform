from __future__ import annotations

from backend.core.contracts.value import CoreValue

from typing import Final, TypeVar

from backend.core.module.component import BaseComponent


ComponentType = TypeVar(
    "ComponentType",
    bound=BaseComponent,
)


class BaseFactory(BaseComponent):
    """
    Canonical component construction registry.

    Owns:
        - constructor registration
        - constructor lookup
        - component creation

    Does not own:
        - lifecycle
        - dependency injection
        - discovery
        - configuration
        - persistence
    """

    VERSION: Final = "8.0"
    COMPONENT_TYPE: Final = "factory"
    CAPABILITIES: Final[tuple[str, ...]] = (
        "register",
        "create",
    )

    def __init__(
        self,
        name: str = "factory",
    ) -> None:
        super().__init__(
            name=name,
            component_type=self.COMPONENT_TYPE,
        )
        self._constructors: dict[
            str,
            type[BaseComponent],
        ] = {}

    def register(
        self,
        name: str,
        component: type[ComponentType],
    ) -> None:
        if not isinstance(name, str):
            raise TypeError("component name must str")

        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("component name required")

        if not isinstance(component, type):
            raise TypeError("component must type")

        if not issubclass(component, BaseComponent):
            raise TypeError("component must BaseComponent")

        if normalized_name in self._constructors:
            raise ValueError(
                f"component already registered: {normalized_name}"
            )

        self._constructors[normalized_name] = component

    def create(
        self,
        name: str,
        *args: CoreValue,
        **kwargs: CoreValue,
    ) -> BaseComponent:
        normalized_name = name.strip()

        constructor = self._constructors.get(
            normalized_name
        )
        if constructor is None:
            raise KeyError(
                f"component not registered: {normalized_name}"
            )

        return constructor(*args, **kwargs)

    def registered(self) -> tuple[str, ...]:
        return tuple(self._constructors)

    def dump(self) -> dict[str, CoreValue]:
        return {
            **super().dump(),
            "factory": {
                "registered": self.registered(),
            },
        }


__all__ = [
    "BaseFactory",
]
