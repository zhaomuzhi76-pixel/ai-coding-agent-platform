from __future__ import annotations

from backend.system.contracts.startup_boundary_contract import (
    SystemStartupModuleProtocol,
)


class SystemStartupAssemblyFactory:
    VERSION = "2.0"

    def create(
        self,
        *,
        startup_module: SystemStartupModuleProtocol,
    ) -> SystemStartupModuleProtocol:
        if not isinstance(
            startup_module,
            SystemStartupModuleProtocol,
        ):
            raise TypeError(
                "invalid system startup module"
            )
        return startup_module

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "SystemStartupAssemblyFactory",
]
