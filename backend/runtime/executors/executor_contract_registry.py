from __future__ import annotations


class ExecutorContractRegistry:
    """
    Runtime executor logical-to-runtime mapping.

    Responsibility:
        - register logical executor contract
        - resolve runtime executor name
        - reject duplicate logical contracts

    Not Responsible:
        - executor instance creation
        - execution
        - scheduling
        - persistence
    """

    VERSION = "3.0"

    def __init__(
        self,
    ) -> None:
        self._contracts: dict[
            str,
            str,
        ] = {}

    def register(
        self,
        executor_type: str,
        runtime_executor: str,
    ) -> None:
        if not isinstance(
            executor_type,
            str,
        ) or not executor_type.strip():
            raise ValueError(
                "executor type required"
            )

        if not isinstance(
            runtime_executor,
            str,
        ) or not runtime_executor.strip():
            raise ValueError(
                "runtime executor required"
            )

        logical_name = executor_type.strip()
        runtime_name = runtime_executor.strip()

        if logical_name in self._contracts:
            raise ValueError(
                "executor contract already registered: "
                f"{logical_name}"
            )

        self._contracts[
            logical_name
        ] = runtime_name

    def resolve(
        self,
        executor_type: str,
    ) -> str:
        if not isinstance(
            executor_type,
            str,
        ) or not executor_type.strip():
            raise ValueError(
                "executor type required"
            )

        logical_name = executor_type.strip()

        runtime_executor = (
            self._contracts.get(
                logical_name
            )
        )

        if runtime_executor is None:
            raise LookupError(
                "executor contract missing:"
                f"{logical_name}"
            )

        return runtime_executor

    def exists(
        self,
        executor_type: str,
    ) -> bool:
        return (
            isinstance(
                executor_type,
                str,
            )
            and executor_type.strip()
            in self._contracts
        )

    def count(
        self,
    ) -> int:
        return len(
            self._contracts
        )

    def all(
        self,
    ) -> dict[str, str]:
        return dict(
            self._contracts
        )

    def ready(
        self,
    ) -> bool:
        return bool(
            self._contracts
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": (
                "ExecutorContractRegistry"
            ),
            "version": self.VERSION,
            "contracts": dict(
                self._contracts
            ),
            "count": self.count(),
            "ready": self.ready(),
        }


__all__ = [
    "ExecutorContractRegistry",
]
