from __future__ import annotations

from typing import Any


class ApplicationStartupModule:
    """
    Assembly-layer lifecycle adapter.

    Responsibility:
        - adapt an injected startup object to the assembly module contract
        - delegate startup lifecycle operations

    Not Responsible:
        - application construction
        - application business logic
        - runtime construction
        - API construction
    """

    VERSION = "2.1"
    NAME = "application.startup"

    def __init__(self, startup: Any) -> None:
        if startup is None:
            raise ValueError("startup required")

        for method in (
            "start",
            "stop",
            "ready",
            "dump",
        ):
            if not callable(
                getattr(startup, method, None)
            ):
                raise TypeError(
                    f"startup must expose {method}()"
                )

        self.startup = startup

    @property
    def name(self) -> str:
        return self.NAME

    @property
    def version(self) -> str:
        return self.VERSION

    def build(
        self,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.startup.start()

        if not self.startup.ready():
            raise RuntimeError(
                "startup lifecycle unavailable"
            )

        result = {
            "startup": self.startup,
        }

        if context is not None:
            context.update(result)

        return result

    def shutdown(self) -> None:
        self.startup.stop()

    def start(self) -> None:
        self.startup.start()

    def stop(self) -> None:
        self.startup.stop()

    def ready(self) -> bool:
        return bool(
            self.startup.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "ready": self.ready(),
            "startup": self.startup.dump(),
        }


__all__ = [
    "ApplicationStartupModule",
]
