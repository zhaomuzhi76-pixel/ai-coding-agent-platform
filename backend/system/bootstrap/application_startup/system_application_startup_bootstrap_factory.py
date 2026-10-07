from __future__ import annotations

from backend.system.bootstrap.application_startup.system_application_startup_bootstrap import (
    SystemApplicationStartupBootstrap,
)
from backend.system.bootstrap.application_startup.system_application_startup_bootstrap_support import (
    SystemApplicationStartupBootstrapSupport,
)


class SystemApplicationStartupBootstrapFactory:
    """
    Construction boundary for system startup coordination.

    Owns only:
        - startup coordinator construction
        - dependency readiness validation
    """

    VERSION = "2.0"

    def create(
        self,
        *,
        startup_module: object,
        runtime: object,
        support: SystemApplicationStartupBootstrapSupport | None = None,
    ) -> SystemApplicationStartupBootstrap:
        active_support = (
            support
            or SystemApplicationStartupBootstrapSupport()
        )

        bootstrap = SystemApplicationStartupBootstrap(
            startup_module=startup_module,
            runtime=runtime,
            support=active_support,
        )

        if not bootstrap.support.ready():
            raise RuntimeError(
                "system application bootstrap support unavailable"
            )

        if bootstrap.started:
            raise RuntimeError(
                "system application bootstrap unexpectedly started"
            )

        return bootstrap

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
    "SystemApplicationStartupBootstrapFactory",
]
