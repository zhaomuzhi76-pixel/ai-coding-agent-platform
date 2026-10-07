from __future__ import annotations

from backend.application.composition.runtime_construction_port import (
    ApplicationRuntimeConstructionProtocol,
)
from backend.application.composition.runtime_port import (
    ApplicationRuntimePortProtocol,
)


class ApplicationRuntimeComposition:
    """
    Application Runtime composition boundary.

    Owns:
        - consumption of Runtime construction port
        - Runtime readiness validation

    Does not own:
        - concrete Runtime construction
        - Runtime plugin construction
        - Runtime execution
        - Runtime lifecycle implementation
    """

    VERSION = "3.0"

    def __init__(
        self,
        *,
        construction: ApplicationRuntimeConstructionProtocol,
    ) -> None:
        if not isinstance(
            construction,
            ApplicationRuntimeConstructionProtocol,
        ):
            raise TypeError(
                "construction must implement "
                "ApplicationRuntimeConstructionProtocol"
            )

        if not construction.ready():
            raise RuntimeError(
                "runtime construction unavailable"
            )

        self.construction = construction
        self.runtime: ApplicationRuntimePortProtocol | None = None

    def create(
        self,
    ) -> ApplicationRuntimePortProtocol:
        runtime = self.construction.create()

        if not isinstance(
            runtime,
            ApplicationRuntimePortProtocol,
        ):
            raise TypeError(
                "constructed runtime must implement "
                "ApplicationRuntimePortProtocol"
            )

        if not runtime.ready():
            raise RuntimeError(
                "runtime component provider unavailable"
            )

        self.runtime = runtime
        return runtime

    def ready(
        self,
    ) -> bool:
        return (
            self.construction.ready()
            and (
                self.runtime is None
                or self.runtime.ready()
            )
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "construction": type(
                self.construction
            ).__name__,
            "runtime": (
                type(self.runtime).__name__
                if self.runtime is not None
                else None
            ),
        }


__all__ = [
    "ApplicationRuntimeComposition",
]
