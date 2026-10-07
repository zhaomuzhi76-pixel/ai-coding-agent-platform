from __future__ import annotations

from collections.abc import Iterable

from backend.assembly.module import AssemblyModule
from backend.assembly.pipeline import AssemblyPipeline
from backend.assembly.registry import AssemblyRegistry
from backend.assembly.runtime import AssemblyRuntime


class AssemblyRuntimeFactory:
    """
    Construction boundary for the canonical assembly runtime.

    Owns only:
        - registry construction
        - module registration
        - pipeline construction
        - runtime construction
        - readiness validation

    Does not own:
        - application startup construction
        - system integration
        - process execution
        - API transport
    """

    VERSION = "1.0"

    def create(
        self,
        *,
        modules: Iterable[AssemblyModule] = (),
    ) -> AssemblyRuntime:
        registry = AssemblyRegistry()

        for module in modules:
            if module is None:
                raise ValueError(
                    "assembly module cannot be None"
                )

            registry.register(module)

        if not registry.ready():
            raise RuntimeError(
                "assembly registry unavailable"
            )

        pipeline = AssemblyPipeline(
            registry
        )

        if not pipeline.ready():
            raise RuntimeError(
                "assembly pipeline unavailable"
            )

        runtime = AssemblyRuntime(
            pipeline
        )

        if not runtime.available():
            raise RuntimeError(
                "assembly runtime unavailable"
            )

        return runtime

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "AssemblyRuntimeFactory",
]
