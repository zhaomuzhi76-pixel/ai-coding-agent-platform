from __future__ import annotations

from typing import Any


class ApplicationInfrastructureComposition:
    """
    Infrastructure composition boundary.

    Owns:
        - infrastructure dependency binding
        - infrastructure resolution

    Does not own:
        - runtime implementation
        - lifecycle startup
        - external services
    """

    VERSION = "1.0"

    def __init__(
        self,
        runtime_construction: Any,
    ) -> None:
        if runtime_construction is None:
            raise ValueError(
                "runtime construction required"
            )

        self.runtime_construction = runtime_construction

    def resolve(
        self,
    ) -> Any:
        return self.runtime_construction

    def ready(
        self,
    ) -> bool:
        checker = getattr(
            self.runtime_construction,
            "ready",
            None,
        )

        if checker is None:
            return False

        return bool(
            checker()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationInfrastructureComposition",
]
