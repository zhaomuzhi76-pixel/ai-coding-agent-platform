from __future__ import annotations

from backend.core.execution import (
    ExecutorProtocol,
)
from backend.runtime.executors.executor_contract_registry import (
    ExecutorContractRegistry,
)
from backend.runtime.executors.registry import (
    ExecutorRegistry,
)


class ExecutorResolver:
    """
    Runtime executor resolver.

    Responsibility:
        - resolve logical executor type
        - map contract to runtime executor

    Not Responsible:
        - executor creation
        - execution
        - scheduling
        - planning
        - persistence
    """

    VERSION = "5.0"

    RESPONSIBILITY = (
        "executor_resolution_boundary",
    )

    def __init__(
        self,
        registry: ExecutorRegistry,
        contract_registry: ExecutorContractRegistry,
    ) -> None:
        if registry is None:
            raise ValueError(
                "executor registry required"
            )

        if contract_registry is None:
            raise ValueError(
                "executor contract registry required"
            )

        self._registry = registry
        self._contract_registry = (
            contract_registry
        )

        self.resolve_count = 0
        self.failure_count = 0

    def resolve_executor(
        self,
        executor_type: str,
    ) -> ExecutorProtocol:
        try:
            runtime_name = (
                self._contract_registry.resolve(
                    executor_type
                )
            )

            executor = self._registry.get(
                runtime_name
            )

            if executor is None:
                raise LookupError(
                    "executor unavailable:"
                    f"{runtime_name}"
                )

            if not executor.ready():
                raise RuntimeError(
                    "executor not ready:"
                    f"{runtime_name}"
                )

            self.resolve_count += 1

            return executor

        except Exception:
            self.failure_count += 1
            raise

    def ready(
        self,
    ) -> bool:
        return (
            self._registry.ready()
            and self._contract_registry.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": "ExecutorResolver",
            "version": self.VERSION,
            "responsibility": (
                self.RESPONSIBILITY
            ),
            "resolve_count": (
                self.resolve_count
            ),
            "failure_count": (
                self.failure_count
            ),
            "ready": self.ready(),
        }


__all__ = [
    "ExecutorResolver",
]
