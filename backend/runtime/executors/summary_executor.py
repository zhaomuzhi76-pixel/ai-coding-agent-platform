from __future__ import annotations

from backend.core.context.kernel_context import (
    KernelContext,
)
from backend.core.execution import (
    ExecutionNodeProtocol,
)
from backend.runtime.executors.summary_builder import (
    RuntimeSummaryBuilder,
)


class SummaryExecutor:
    """
    Runtime summary executor.

    Responsibility:
        - execute summary node
        - build runtime summary result

    Not Responsible:
        - node lifecycle
        - DAG scheduling
        - runtime output storage
        - persistence
    """

    VERSION = "3.1"

    name = "summary"

    def __init__(
        self,
        builder: RuntimeSummaryBuilder | None = None,
    ) -> None:
        self.builder = (
            builder
            or RuntimeSummaryBuilder()
        )
        self.execution_count = 0

    async def execute(
        self,
        node: ExecutionNodeProtocol,
        context: KernelContext,
    ) -> dict[str, object]:
        if not isinstance(
            node,
            ExecutionNodeProtocol,
        ):
            raise TypeError(
                "summary node must ExecutionNodeProtocol"
            )

        self.execution_count += 1

        previous: dict[str, object] = {}

        if context is not None:
            value = context.outputs

            if isinstance(
                value,
                dict,
            ):
                previous = value

        result = self.builder.build(
            {
                "status": "success",
                "result": previous,
                "metadata": {
                    "executor": self.name,
                },
            }
        )

        return {
            "executor": self.name,
            "status": "success",
            "result": result,
        }

    def ready(
        self,
    ) -> bool:
        return self.builder is not None

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.VERSION,
            "ready": self.ready(),
            "execution_count": (
                self.execution_count
            ),
        }


__all__ = [
    "SummaryExecutor",
]
