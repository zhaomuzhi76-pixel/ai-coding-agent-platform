from __future__ import annotations

from typing import Any


class AssemblyModule:
    """
    Cross-layer system assembly module.

    Concrete composition remains external to this framework.
    """

    VERSION = "1.0"

    def __init__(
        self,
        name: str,
    ) -> None:
        if not name:
            raise ValueError(
                "assembly module name required"
            )
        self.name = name
        self.version = self.VERSION
        self.result: Any = None

    def build(
        self,
        context: Any = None,
    ) -> Any:
        raise NotImplementedError(
            "assembly module build() must be implemented"
        )

    def ready(self) -> bool:
        return bool(self.name)

    def dump(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "ready": self.ready(),
            "built": self.result is not None,
        }


__all__ = [
    "AssemblyModule",
]
