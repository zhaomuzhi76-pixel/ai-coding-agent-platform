from __future__ import annotations

from backend.system.composition.system import (
    SystemComposition,
)
from backend.system.contracts.assembly_boundary_contract import (
    SystemAssemblyRuntimeProtocol,
)
from backend.system.integration.runtime import (
    SystemIntegrationRuntime,
)


class SystemIntegrationRuntimeFactory:
    VERSION = "3.0"

    def create(
        self,
        *,
        assembly_runtime: SystemAssemblyRuntimeProtocol,
        system: SystemComposition,
    ) -> SystemIntegrationRuntime:
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

        runtime = SystemIntegrationRuntime(
            assembly_runtime=assembly_runtime,
            system=system,
        )

        if not isinstance(
            runtime,
            SystemIntegrationRuntime,
        ):
            raise TypeError(
                "system integration runtime construction failed"
            )

        return runtime

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "SystemIntegrationRuntimeFactory",
]
