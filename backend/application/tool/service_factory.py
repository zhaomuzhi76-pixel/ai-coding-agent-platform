from __future__ import annotations

from backend.application.composition.tool_runtime_port import (
    ApplicationToolRuntimeProtocol,
)
from backend.application.tool.service import (
    ToolApplicationService,
)


class ToolApplicationServiceFactory:
    """
    Sole construction owner for ToolApplicationService.
    """

    VERSION = "2.0"

    def create(
        self,
        *,
        capability: ApplicationToolRuntimeProtocol,
    ) -> ToolApplicationService:
        if not isinstance(
            capability,
            ApplicationToolRuntimeProtocol,
        ):
            raise TypeError(
                "capability must implement "
                "ApplicationToolRuntimeProtocol"
            )

        service = ToolApplicationService(
            capability=capability,
        )

        self._validate(service)
        return service

    @staticmethod
    def _validate(
        service: ToolApplicationService,
    ) -> None:
        for name in (
            "execute",
            "ready",
            "dump",
        ):
            if not callable(
                getattr(service, name, None)
            ):
                raise TypeError(
                    "tool application service must expose "
                    f"{name}()"
                )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ToolApplicationServiceFactory",
]
