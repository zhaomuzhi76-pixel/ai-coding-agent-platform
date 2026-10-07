from __future__ import annotations

from typing import Final


class BaseLifecycle:
    """
    Canonical lifecycle hooks.

    Owns:
        - lifecycle callbacks

    Does not own:
        - lifecycle state
        - readiness
        - snapshot
        - orchestration
    """

    VERSION: Final = "8.0"

    RESPONSIBILITY: Final = (
        "lifecycle_hooks",
    )

    def initialize(
        self,
    ) -> None:
        self.on_initialize()

    def start(
        self,
    ) -> None:
        self.on_start()

    def stop(
        self,
    ) -> None:
        self.on_stop()

    def destroy(
        self,
    ) -> None:
        self.on_destroy()

    def on_initialize(
        self,
    ) -> None:
        pass

    def on_start(
        self,
    ) -> None:
        pass

    def on_stop(
        self,
    ) -> None:
        pass

    def on_destroy(
        self,
    ) -> None:
        pass


__all__ = [
    "BaseLifecycle",
]
