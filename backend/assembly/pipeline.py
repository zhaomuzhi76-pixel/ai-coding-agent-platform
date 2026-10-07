from __future__ import annotations

from typing import Any

from backend.assembly.registry import (
    AssemblyRegistry,
)


class AssemblyPipeline:
    """
    Ordered cross-layer assembly pipeline.

    Owns:
        - ordered module build
        - post-build readiness validation
        - partial-build rollback
        - reverse-order module shutdown
    """

    VERSION = "1.3"

    def __init__(
        self,
        registry: AssemblyRegistry,
    ) -> None:
        if registry is None:
            raise ValueError(
                "assembly registry required"
            )

        self.registry = registry
        self.results: dict[str, Any] = {}

    def build(
        self,
        context: Any = None,
    ) -> dict[str, Any]:
        if not self.registry.ready():
            raise RuntimeError(
                "assembly registry unavailable"
            )

        self.results.clear()
        built: list[str] = []

        try:
            for name in self.registry.names():
                module = self.registry.resolve(name)

                result = module.build(
                    context
                )

                if not module.ready():
                    raise RuntimeError(
                        "assembly module unavailable after build: "
                        f"{name}"
                    )

                self.results[name] = result
                built.append(name)

        except Exception:
            self._rollback_built_modules(
                built
            )
            self.results.clear()
            raise

        return dict(self.results)

    def shutdown(
        self,
    ) -> None:
        failures: list[
            tuple[str, Exception]
        ] = []

        for name in reversed(
            tuple(self.results)
        ):
            module = self.registry.resolve(name)

            try:
                self._shutdown_module(
                    module
                )
            except Exception as error:
                failures.append(
                    (name, error)
                )

        self.results.clear()

        if failures:
            name, error = failures[0]
            raise RuntimeError(
                "assembly module shutdown failed: "
                f"{name}"
            ) from error

    def ready(
        self,
    ) -> bool:
        return self.registry.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "registry": self.registry.dump(),
            "built": tuple(self.results),
            "ready": self.ready(),
        }

    def _rollback_built_modules(
        self,
        built: list[str],
    ) -> None:
        for name in reversed(built):
            module = self.registry.resolve(name)

            try:
                self._shutdown_module(
                    module
                )
            except Exception:
                pass

    @staticmethod
    def _shutdown_module(
        module: object,
    ) -> None:
        shutdown = getattr(
            module,
            "shutdown",
            None,
        )
        stop = getattr(
            module,
            "stop",
            None,
        )

        if callable(shutdown):
            shutdown()
            return

        if callable(stop):
            stop()


__all__ = [
    "AssemblyPipeline",
]
