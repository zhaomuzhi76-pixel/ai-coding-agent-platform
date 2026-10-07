from __future__ import annotations


class RuntimePluginRegistry:
    """
    Single runtime plugin registry.

    Responsibility:
        - register plugin instances
        - resolve registered plugins
        - expose plugin inventory

    Not Responsible:
        - plugin loading
        - lifecycle
        - capability registration
        - execution
    """

    VERSION = "3.0"

    def __init__(self) -> None:
        self._items: dict[
            str,
            dict[str, object],
        ] = {}

    def register(
        self,
        *,
        category: str,
        name: str,
        component: object,
        version: str = "1.0",
    ) -> None:
        if not category:
            raise ValueError(
                "plugin category required"
            )

        if not name:
            raise ValueError(
                "plugin name required"
            )

        if component is None:
            raise ValueError(
                "plugin component required"
            )

        key = f"{category}.{name}"

        if key in self._items:
            raise ValueError(
                f"plugin already registered: {key}"
            )

        self._items[key] = {
            "category": category,
            "name": name,
            "component": component,
            "version": version,
        }

    def resolve(
        self,
        category: str,
        name: str,
    ) -> object:
        key = f"{category}.{name}"

        try:
            return self._items[key]["component"]
        except KeyError as error:
            raise LookupError(
                f"plugin not found: {category}/{name}"
            ) from error

    def list(
        self,
    ) -> dict[str, tuple[str, ...]]:
        result: dict[
            str,
            list[str],
        ] = {}

        for item in self._items.values():
            category = str(
                item["category"]
            )
            result.setdefault(
                category,
                [],
            ).append(
                str(item["name"])
            )

        return {
            category: tuple(names)
            for category, names
            in result.items()
        }

    def names(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            self._items
        )

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "plugins": self.list(),
            "ready": self.ready(),
        }


__all__ = [
    "RuntimePluginRegistry",
]
