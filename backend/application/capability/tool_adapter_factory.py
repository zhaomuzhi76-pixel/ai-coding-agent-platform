from __future__ import annotations

from backend.application.capability.tool_adapter import (
    ToolApplicationCapabilityAdapter,
)
from backend.application.tool.service import (
    ToolApplicationService,
)


class ToolApplicationCapabilityAdapterFactory:
    """
    Sole construction owner for ToolApplicationCapabilityAdapter.
    """

    VERSION = "1.0"

    def create(
        self,
        *,
        service: ToolApplicationService,
    ) -> ToolApplicationCapabilityAdapter:
        if not self.ready():
            raise RuntimeError(
                "tool capability adapter factory unavailable"
            )

        if not isinstance(
            service,
            ToolApplicationService,
        ):
            raise TypeError(
                "service must ToolApplicationService"
            )

        adapter = ToolApplicationCapabilityAdapter(
            service
        )

        self._validate(adapter)
        return adapter

    @staticmethod
    def _validate(
        adapter: ToolApplicationCapabilityAdapter,
    ) -> None:
        for name in (
            "execute",
            "initialize",
            "shutdown",
            "ready",
            "dump",
        ):
            if not callable(
                getattr(adapter, name, None)
            ):
                raise TypeError(
                    "tool capability adapter must expose "
                    f"{name}()"
                )

        if not adapter.ready():
            raise RuntimeError(
                "tool capability adapter unavailable"
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
    "ToolApplicationCapabilityAdapterFactory",
]
