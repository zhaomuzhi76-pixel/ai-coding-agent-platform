from __future__ import annotations

from backend.core.result import ExecutionResult
from backend.runtime.plugins.intelligence.memory_emitter import (
    MemoryWriteEmitter,
)


class ResultMemoryProcessor:
    """
    Execution result memory processor.

    Responsibility:
        - extract learning information from ExecutionResult
        - emit memory_write event

    Not Responsible:
        - memory persistence
        - retrieval
        - embedding
        - event dispatch
        - generic processor framework ownership
    """

    VERSION = "1.1"

    def __init__(
        self,
        emitter: MemoryWriteEmitter,
    ) -> None:
        if emitter is None:
            raise ValueError(
                "memory emitter required"
            )

        self.emitter = emitter
        self.process_count = 0

    async def process(
        self,
        result: ExecutionResult,
    ) -> ExecutionResult:
        if not isinstance(
            result,
            ExecutionResult,
        ):
            raise TypeError(
                "ExecutionResult required"
            )

        if result.outputs:
            await self.emitter.emit(
                change="runtime_execution",
                result=str(result.outputs),
                lesson=(
                    "execution result stored as "
                    "intelligence memory"
                ),
            )
            self.process_count += 1

        return result

    def ready(
        self,
    ) -> bool:
        return self.emitter.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "process_count": self.process_count,
            "ready": self.ready(),
        }


__all__ = [
    "ResultMemoryProcessor",
]
