from __future__ import annotations

from dataclasses import dataclass, field

from backend.core.errors import CoreErrorDetail


@dataclass
class NodeExecutionResult:
    """
    Runtime node execution result value.

    Owns:
        - node execution success/failure
        - output value
        - canonical error
        - metadata

    Does not own:
        - execution
        - retry
        - scheduling
        - persistence
    """

    VERSION = "2.0"

    node_id: str
    success: bool
    output: object | None = None
    error: CoreErrorDetail | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.node_id, str) or not self.node_id.strip():
            raise ValueError("node id required")
        if not isinstance(self.success, bool):
            raise TypeError("success must bool")
        if self.error is not None and not isinstance(
            self.error,
            CoreErrorDetail,
        ):
            raise TypeError("error must CoreErrorDetail or None")
        if self.success and self.error is not None:
            raise ValueError("successful result cannot contain error")
        if not self.success and self.error is None:
            raise ValueError("failed result requires canonical error")
        if not isinstance(self.metadata, dict):
            raise TypeError("metadata must dict")

    @classmethod
    def succeeded(
        cls,
        node_id: str,
        output: object | None = None,
        metadata: dict[str, object] | None = None,
    ) -> "NodeExecutionResult":
        return cls(
            node_id=node_id,
            success=True,
            output=output,
            metadata=dict(metadata or {}),
        )

    @classmethod
    def failed(
        cls,
        node_id: str,
        error: CoreErrorDetail,
        metadata: dict[str, object] | None = None,
    ) -> "NodeExecutionResult":
        if not isinstance(error, CoreErrorDetail):
            raise TypeError("failed result error must CoreErrorDetail")
        return cls(
            node_id=node_id,
            success=False,
            error=error,
            metadata=dict(metadata or {}),
        )

    def ready(self) -> bool:
        return (
            bool(self.node_id.strip())
            and isinstance(self.success, bool)
            and (
                self.error is None
                or self.error.ready()
            )
        )

    def failed_result(self) -> bool:
        return not self.success

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "node_id": self.node_id,
            "success": self.success,
            "output": self.output,
            "error": (
                self.error.dump()
                if self.error is not None
                else None
            ),
            "metadata": dict(self.metadata),
            "ready": self.ready(),
        }


__all__ = ["NodeExecutionResult"]
