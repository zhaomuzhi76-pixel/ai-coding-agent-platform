from __future__ import annotations

from backend.runtime.errors.error_adapter import (
    RuntimeErrorAdapter,
)
from backend.runtime.errors.normalization_bridge import (
    RuntimeErrorNormalizationBridge,
)
from backend.runtime.errors.normalization_contract import (
    RuntimeErrorNormalizationProtocol,
)


class RuntimeErrorNormalizationComposition:
    """
    Runtime error normalization assembly boundary.

    Responsibility:
        - assemble the canonical normalization bridge
        - expose the normalized error contract

    Not Responsible:
        - exception classification
        - runtime execution
        - transport formatting
        - application business logic
    """

    VERSION = "1.0"

    def __init__(
        self,
        bridge: RuntimeErrorNormalizationProtocol | None = None,
    ) -> None:
        self.bridge = (
            bridge
            if bridge is not None
            else self._create_default()
        )

        if not isinstance(
            self.bridge,
            RuntimeErrorNormalizationProtocol,
        ):
            raise TypeError(
                "runtime error normalization contract required"
            )

    def create(
        self,
    ) -> RuntimeErrorNormalizationProtocol:
        if not self.bridge.ready():
            raise RuntimeError(
                "runtime error normalization unavailable"
            )

        return self.bridge

    def ready(
        self,
    ) -> bool:
        return self.bridge.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "bridge": self.bridge.dump(),
            "ready": self.ready(),
        }

    @staticmethod
    def _create_default(
    ) -> RuntimeErrorNormalizationBridge:
        return RuntimeErrorNormalizationBridge(
            adapter=RuntimeErrorAdapter()
        )


__all__ = [
    "RuntimeErrorNormalizationComposition",
]
