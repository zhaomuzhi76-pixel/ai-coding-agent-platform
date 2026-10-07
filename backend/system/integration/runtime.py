from __future__ import annotations

from typing import Any

from backend.system.composition.system import SystemComposition
from backend.system.contracts.assembly_boundary_contract import (
    SystemAssemblyRuntimeProtocol,
)


class SystemIntegrationRuntime:
    """
    Top-level system integration runtime.

    Coordinates injected assembly and system contracts without
    depending on concrete Assembly implementations.
    """

    VERSION = "1.3"
    NAME = "system.integration.runtime"

    def __init__(
        self,
        *,
        assembly_runtime: SystemAssemblyRuntimeProtocol,
        system: SystemComposition,
    ) -> None:
        if not isinstance(
            assembly_runtime,
            SystemAssemblyRuntimeProtocol,
        ):
            raise TypeError(
                "assembly runtime contract required"
            )

        if not isinstance(
            system,
            SystemComposition,
        ):
            raise TypeError(
                "system must be SystemComposition"
            )

        self.assembly_runtime = assembly_runtime
        self.system = system
        self.started = False
        self.results: dict[str, Any] = {}

    def start(
        self,
        context: Any = None,
    ) -> dict[str, Any]:
        if self.started:
            return dict(self.results)

        if not self.assembly_runtime.available():
            raise RuntimeError(
                "assembly runtime unavailable"
            )

        try:
            assembly_result = (
                self.assembly_runtime.start(
                    context
                )
            )

            if not self.assembly_runtime.ready():
                raise RuntimeError(
                    "assembly runtime unavailable after start"
                )

            self.system.start()

            if not self.system.ready():
                raise RuntimeError(
                    "system integration unavailable"
                )

            self.results = {
                "assembly": dict(
                    assembly_result
                ),
                "system": self.system.snapshot(),
            }
            self.started = True

            return dict(self.results)

        except Exception:
            self.stop()
            raise

    def stop(self) -> None:
        system = self.system
        assembly = self.assembly_runtime

        self.started = False
        self.results.clear()

        try:
            system.stop()
        finally:
            assembly.stop()

    def ready(
        self,
    ) -> bool:
        return (
            self.started
            and self.assembly_runtime.ready()
            and self.system.ready()
        )

    def snapshot(self):
        return self.system.snapshot()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.NAME,
            "version": self.VERSION,
            "started": self.started,
            "ready": self.ready(),
            "assembly_runtime": (
                self.assembly_runtime.dump()
            ),
            "system": self.system.dump(),
            "built": tuple(
                self.results
            ),
        }


__all__ = [
    "SystemIntegrationRuntime",
]
