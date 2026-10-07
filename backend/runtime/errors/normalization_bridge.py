from __future__ import annotations

from backend.core.errors import CoreErrorDetail
from backend.runtime.errors.error_adapter import (
    RuntimeErrorAdapter,
)
from backend.runtime.errors.error_adapter_protocol import (
    RuntimeErrorAdapterProtocol,
)
from backend.runtime.errors.normalization_contract import (
    RuntimeErrorNormalizationProtocol,
)


class RuntimeErrorNormalizationBridge(
    RuntimeErrorNormalizationProtocol,
):
    """
    Canonical Runtime-to-Core error normalization owner.

    Ownership:
        - own the runtime normalization boundary
        - delegate exception classification to RuntimeErrorAdapter
        - return canonical CoreErrorDetail

    Not Responsible:
        - exception classification implementation
        - runtime execution
        - transport formatting
        - application policy
        - logging
    """

    VERSION = "1.0"

    def __init__(
        self,
        adapter: RuntimeErrorAdapterProtocol | None = None,
    ) -> None:
        self.adapter = (
            adapter
            if adapter is not None
            else RuntimeErrorAdapter()
        )

        if not isinstance(
            self.adapter,
            RuntimeErrorAdapterProtocol,
        ):
            raise TypeError(
                "runtime error adapter contract required"
            )

    def normalize(
        self,
        error: BaseException,
        *,
        operation: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> CoreErrorDetail:
        if error is None:
            raise ValueError(
                "runtime error required"
            )

        if not isinstance(
            error,
            BaseException,
        ):
            raise TypeError(
                "runtime error must BaseException"
            )

        if operation is not None:
            if not isinstance(
                operation,
                str,
            ):
                raise TypeError(
                    "operation must str or None"
                )

            operation = operation.strip() or None

        if metadata is not None:
            if not isinstance(
                metadata,
                dict,
            ):
                raise TypeError(
                    "metadata must dict or None"
                )

            metadata = dict(
                metadata
            )

        if not self.adapter.ready():
            raise RuntimeError(
                "runtime error adapter not ready"
            )

        return self.adapter.adapt(
            error,
            operation=operation,
            metadata=metadata,
        )

    def ready(
        self,
    ) -> bool:
        return self.adapter.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "adapter": self.adapter.dump(),
        }


__all__ = [
    "RuntimeErrorNormalizationBridge",
]
