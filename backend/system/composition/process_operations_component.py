from __future__ import annotations

from backend.process_operations.process_operations_contract import (
    ProcessOperationsContract,
)


class ProcessOperationsComponent:
    """
    Adapt ProcessOperations to the System component boundary.

    Owns only:
        - system component identity
        - readiness projection
        - diagnostic projection

    Does not own:
        - process execution
        - process lifecycle
        - process health implementation
    """

    VERSION = "1.0"

    def __init__(
        self,
        operations: ProcessOperationsContract,
    ) -> None:
        if not isinstance(
            operations,
            ProcessOperationsContract,
        ):
            raise TypeError(
                "process operations contract required"
            )

        self.operations = operations

    @property
    def name(self) -> str:
        return "process.operations"

    @property
    def version(self) -> str:
        return self.VERSION

    def ready(self) -> bool:
        return bool(
            self.operations.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "ready": self.ready(),
            "operations": self.operations.dump(),
        }


__all__ = [
    "ProcessOperationsComponent",
]
