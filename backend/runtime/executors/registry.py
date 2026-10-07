from __future__ import annotations

from backend.core.execution import ExecutorProtocol


class ExecutorRegistry:
    """Runtime executor registry."""

    VERSION = "7.1"

    def __init__(self) -> None:
        self._executors: dict[str, ExecutorProtocol] = {}

    def register(
        self,
        name: str,
        executor: ExecutorProtocol,
    ) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("executor name required")
        if executor is None:
            raise ValueError("executor required")

        normalized_name = name.strip()
        self._validate_executor(executor)

        if normalized_name in self._executors:
            raise ValueError(
                f"executor already registered: {normalized_name}"
            )

        if executor.name != normalized_name:
            raise ValueError(
                f"executor identity mismatch: "
                f"{normalized_name}!={executor.name}"
            )

        self._executors[normalized_name] = executor

    def get(
        self,
        name: str,
    ) -> ExecutorProtocol | None:
        if not isinstance(name, str):
            return None
        return self._executors.get(name.strip())

    def exists(self, name: str) -> bool:
        return isinstance(name, str) and name.strip() in self._executors

    def names(self) -> list[str]:
        return list(self._executors)

    def all(self) -> dict[str, ExecutorProtocol]:
        return dict(self._executors)

    def count(self) -> int:
        return len(self._executors)

    @staticmethod
    def _validate_executor(
        executor: ExecutorProtocol,
    ) -> None:
        if not isinstance(executor, ExecutorProtocol):
            raise TypeError(
                "executor must implement ExecutorProtocol"
            )
        if not executor.name:
            raise ValueError("executor name missing")
        if not callable(executor.execute):
            raise TypeError("executor execute missing")
        if not callable(executor.ready):
            raise TypeError("executor ready missing")
        if not callable(executor.dump):
            raise TypeError("executor dump missing")

    def ready(self) -> bool:
        return bool(self._executors) and all(
            executor.ready()
            for executor in self._executors.values()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "executors": self.names(),
            "count": self.count(),
            "ready": self.ready(),
        }


__all__ = ["ExecutorRegistry"]
