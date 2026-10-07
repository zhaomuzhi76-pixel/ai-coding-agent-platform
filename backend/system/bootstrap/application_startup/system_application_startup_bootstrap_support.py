from __future__ import annotations

from backend.system.contracts.startup_boundary_contract import (
    SystemIntegrationRuntimeProtocol,
    SystemStartupModuleProtocol,
    SystemStartupProtocol,
)


class SystemApplicationStartupBootstrapSupport:
    VERSION = "3.0"

    def validate_startup_module(
        self,
        startup_module: object,
    ) -> SystemStartupModuleProtocol:
        if not isinstance(
            startup_module,
            SystemStartupModuleProtocol,
        ):
            raise TypeError(
                "invalid system startup module"
            )
        return startup_module

    def validate_runtime(
        self,
        runtime: object,
    ) -> SystemIntegrationRuntimeProtocol:
        if not isinstance(
            runtime,
            SystemIntegrationRuntimeProtocol,
        ):
            raise TypeError(
                "invalid system integration runtime"
            )
        return runtime

    def startup(
        self,
        startup_module: SystemStartupModuleProtocol,
    ) -> SystemStartupProtocol:
        startup = startup_module.startup

        if not isinstance(
            startup,
            SystemStartupProtocol,
        ):
            raise TypeError(
                "startup module exposes invalid startup"
            )

        if not startup.ready():
            raise RuntimeError(
                "startup not ready"
            )

        return startup

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "SystemApplicationStartupBootstrapSupport",
]
