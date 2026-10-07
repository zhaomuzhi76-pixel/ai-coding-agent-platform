from __future__ import annotations

from backend.core.contracts.value import CoreValue

from backend.core.errors import CoreErrorDetail
from backend.core.result.value import (
    ResultMetadata,
    ResultOutput,
    is_result_value,
)


class ExecutionResult:
    """
    Core-owned stable execution result entity.

    Owns outputs, terminal status, canonical error and metadata.
    Does not own error handling, normalization, serialization,
    persistence, response formatting or execution.
    """

    VERSION = "2.1"
    RESPONSIBILITY = ("execution_result_entity",)

    def __init__(
        self,
        *,
        outputs: list[ResultOutput] | None = None,
        final: ResultOutput = None,
        model: str | None = None,
        success: bool = True,
        error: CoreErrorDetail | None = None,
        metadata: ResultMetadata | None = None,
    ) -> None:
        if outputs is not None and not isinstance(outputs, list):
            raise TypeError("outputs must list")

        normalized_outputs = list(outputs or [])
        for index, output in enumerate(normalized_outputs):
            if not is_result_value(output):
                raise TypeError(
                    f"outputs[{index}] must be ResultValue"
                )

        if final is not None and not is_result_value(final):
            raise TypeError("final must be ResultValue or None")
        if model is not None and not isinstance(model, str):
            raise TypeError("model must str or None")
        if not isinstance(success, bool):
            raise TypeError("success must bool")
        if error is not None and not isinstance(error, CoreErrorDetail):
            raise TypeError(
                "error must CoreErrorDetail or None"
            )
        if success and error is not None:
            raise ValueError(
                "successful result cannot contain error"
            )
        if not success and error is None:
            raise ValueError(
                "failed result requires canonical error"
            )

        normalized_metadata = dict(metadata or {})
        for key, value in normalized_metadata.items():
            if not isinstance(key, str):
                raise TypeError("metadata keys must str")
            if not is_result_value(value):
                raise TypeError(
                    f"metadata[{key}] must be ResultValue"
                )

        self.outputs = normalized_outputs
        self.final = final
        self.model = model
        self.success = success
        self.error = error
        self.metadata = normalized_metadata

    def ready(self) -> bool:
        return (
            isinstance(self.outputs, list)
            and all(is_result_value(item) for item in self.outputs)
            and (
                self.final is None
                or is_result_value(self.final)
            )
            and isinstance(self.metadata, dict)
            and all(
                isinstance(key, str) and is_result_value(value)
                for key, value in self.metadata.items()
            )
            and isinstance(self.success, bool)
            and (
                self.error is None
                or self.error.ready()
            )
            and not (
                self.success and self.error is not None
            )
            and not (
                not self.success and self.error is None
            )
        )

    def ok(self) -> bool:
        return self.success

    def failed(self) -> bool:
        return not self.success

    def has_error(self) -> bool:
        return self.error is not None

    def empty(self) -> bool:
        return not bool(self.outputs)

    def count(self) -> int:
        return len(self.outputs)

    def dump(self) -> dict[str, CoreValue]:
        return {
            "name": "ExecutionResult",
            "version": self.VERSION,
            "responsibility": list(self.RESPONSIBILITY),
            "ready": self.ready(),
            "success": self.success,
            "outputs": list(self.outputs),
            "final": self.final,
            "model": self.model,
            "error": (
                self.error.dump()
                if self.error is not None
                else None
            ),
            "metadata": dict(self.metadata),
            "output_count": self.count(),
        }


__all__ = [
    "ExecutionResult",
]
