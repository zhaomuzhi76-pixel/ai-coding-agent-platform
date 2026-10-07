from __future__ import annotations

from typing import Any

from backend.assembly.lifecycle import (
    AssemblyLifecycle,
    AssemblyLifecycleState,
)
from backend.assembly.pipeline import (
    AssemblyPipeline,
)


class AssemblyRuntime:
    """
    System assembly runtime boundary.

    Owns:
        - assembly lifecycle
        - pipeline build
        - pipeline shutdown
        - idempotent started-state reentry
    """

    VERSION = "1.2"

    def __init__(
        self,
        pipeline: AssemblyPipeline,
        lifecycle: AssemblyLifecycle | None = None,
    ) -> None:
        if pipeline is None:
            raise ValueError(
                "assembly pipeline required"
            )

        self.pipeline = pipeline
        self.lifecycle = (
            lifecycle
            or AssemblyLifecycle()
        )
        self.results: dict[str, Any] = {}

    def start(
        self,
        context: Any = None,
    ) -> dict[str, Any]:
        if (
            self.lifecycle.state
            is AssemblyLifecycleState.STARTED
        ):
            return dict(self.results)

        if not self.pipeline.ready():
            raise RuntimeError(
                "assembly pipeline unavailable"
            )

        try:
            self.lifecycle.start()
            self.results = self.pipeline.build(
                context
            )
            return dict(self.results)
        except Exception:
            self.lifecycle.fail()
            raise

    def stop(
        self,
    ) -> None:
        try:
            self.pipeline.shutdown()
        finally:
            self.results.clear()

            if (
                self.lifecycle.state
                is AssemblyLifecycleState.STARTED
            ):
                self.lifecycle.stop()

    def available(
        self,
    ) -> bool:
        return (
            self.pipeline.ready()
            and self.lifecycle.state
            in (
                AssemblyLifecycleState.CREATED,
                AssemblyLifecycleState.STOPPED,
                AssemblyLifecycleState.FAILED,
            )
        )

    def ready(
        self,
    ) -> bool:
        return (
            self.pipeline.ready()
            and self.lifecycle.state
            is AssemblyLifecycleState.STARTED
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "lifecycle": self.lifecycle.dump(),
            "pipeline": self.pipeline.dump(),
            "built": tuple(self.results),
            "available": self.available(),
            "ready": self.ready(),
        }


__all__ = [
    "AssemblyRuntime",
]
