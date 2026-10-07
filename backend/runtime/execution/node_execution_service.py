from __future__ import annotations

from backend.core.context.kernel_context import KernelContext
from backend.core.execution import ExecutorProtocol, ExecutionNodeProtocol
from backend.runtime.execution.execution_contracts import ExecutorResolverProtocol


class NodeExecutionService:
    """
    Runtime internal single-node execution service.

    Owns:
        - executor resolution
        - executor invocation
    """

    VERSION = "43.0"
    RESPONSIBILITY = ("runtime_executor_invocation",)

    def __init__(
        self,
        executor_resolver: ExecutorResolverProtocol,
    ) -> None:
        if executor_resolver is None:
            raise ValueError("executor resolver required")
        self.executor_resolver = executor_resolver

    async def execute(
        self,
        node: ExecutionNodeProtocol,
        context: KernelContext,
    ) -> object:
        if not isinstance(node, ExecutionNodeProtocol):
            raise TypeError("node must ExecutionNodeProtocol")
        if context is None:
            raise ValueError("context required")

        executor = self.executor_resolver.resolve_executor(
            node.executor_type
        )

        if not isinstance(executor, ExecutorProtocol):
            raise TypeError(
                "resolved executor must implement ExecutorProtocol"
            )

        return await executor.execute(node, context)

    def ready(self) -> bool:
        return self.executor_resolver.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "executor_resolver": type(
                self.executor_resolver
            ).__name__,
        }


__all__ = ["NodeExecutionService"]
