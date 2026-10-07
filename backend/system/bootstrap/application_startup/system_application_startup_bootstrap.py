from __future__ import annotations

from backend.system.bootstrap.application_startup.system_application_startup_bootstrap_contract import (
    SystemApplicationStartupBootstrapContract,
)
from backend.system.bootstrap.application_startup.system_application_startup_bootstrap_support import (
    SystemApplicationStartupBootstrapSupport,
)
from backend.system.contracts.startup_boundary_contract import (
    SystemIntegrationRuntimeProtocol,
    SystemStartupModuleProtocol,
    SystemStartupProtocol,
)


class SystemApplicationStartupBootstrap(
    SystemApplicationStartupBootstrapContract,
):
    VERSION = "3.0"

    def __init__(
        self,
        *,
        startup_module: SystemStartupModuleProtocol,
        runtime: SystemIntegrationRuntimeProtocol,
        support: SystemApplicationStartupBootstrapSupport | None = None,
    ) -> None:
        self.support = (
            support
            or SystemApplicationStartupBootstrapSupport()
        )
        self.startup_module = (
            self.support.validate_startup_module(
                startup_module
            )
        )
        self.runtime = self.support.validate_runtime(
            runtime
        )
        self._startup: SystemStartupProtocol | None = None
        self.started = False
        self.start_count = 0
        self.stop_count = 0

    def start(self) -> object:
        if self.started:
            return self._startup

        self.runtime.start()

        try:
            startup = self.support.startup(
                self.startup_module
            )
        except Exception:
            self.runtime.stop()
            raise

        self._startup = startup
        self.started = True
        self.start_count += 1
        return startup

    def stop(self) -> None:
        if not self.started:
            return

        try:
            self.runtime.stop()
        finally:
            self._startup = None
            self.started = False
            self.stop_count += 1

    def startup(self) -> SystemStartupProtocol | None:
        return self._startup

    def integration_runtime(self) -> object:
        return self.runtime

    def ready(self) -> bool:
        return (
            self.support.ready()
            and self.started
            and self._startup is not None
            and self._startup.ready()
            and self.runtime.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "started": self.started,
            "start_count": self.start_count,
            "stop_count": self.stop_count,
            "startup": (
                type(self._startup).__name__
                if self._startup is not None
                else None
            ),
            "integration_runtime": type(
                self.runtime
            ).__name__,
            "runtime": self.runtime.dump(),
        }


__all__ = [
    "SystemApplicationStartupBootstrap",
]
