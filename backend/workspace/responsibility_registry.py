from __future__ import annotations

from typing import Any


class ResponsibilityRegistry:
    """
    Workspace responsibility index.

    Responsibility:
        - store responsibility metadata
        - query registered modules
        - maintain responsibility index

    Not Responsible:
        - filesystem scanning
        - source parsing
        - responsibility extraction
        - similarity calculation
        - duplicate analysis
    """

    VERSION = "1.0"

    RESPONSIBILITY = (
        "workspace_responsibility_registry"
    )

    def __init__(self) -> None:
        self._items: dict[str, dict[str, Any]] = {}

    def register(
        self,
        item: dict[str, Any],
    ) -> None:

        path = str(
            item.get(
                "path",
                "",
            )
        )

        if not path:
            return

        self._items[path] = dict(
            item
        )

    def register_many(
        self,
        items: list[dict[str, Any]],
    ) -> None:

        for item in items:
            self.register(
                item
            )

    def remove(
        self,
        path: str,
    ) -> None:

        self._items.pop(
            path,
            None,
        )

    def find_by_path(
        self,
        path: str,
    ) -> dict[str, Any] | None:

        return self._items.get(
            path
        )

    def find_by_responsibility(
        self,
        responsibility: str,
    ) -> list[dict[str, Any]]:

        result = []

        for item in self._items.values():

            responsibilities = item.get(
                "responsibilities",
                [],
            )

            if responsibility in responsibilities:
                result.append(
                    item
                )

        return result

    def all(
        self,
    ) -> list[dict[str, Any]]:

        return list(
            self._items.values()
        )

    def count(
        self,
    ) -> int:

        return len(
            self._items
        )

    def clear(
        self,
    ) -> None:

        self._items.clear()

    def ready(
        self,
    ) -> bool:

        return True

    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name":
                "ResponsibilityRegistry",

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "count":
                self.count(),

            "ready":
                self.ready(),
        }


__all__ = [
    "ResponsibilityRegistry",
]
