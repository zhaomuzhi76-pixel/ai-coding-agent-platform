from __future__ import annotations

from dataclasses import replace

from backend.core.execution import (
    ExecutionNodeProtocol,
)
from backend.runtime.executors.tool_call_resolver import (
    ToolCallResolver,
)
from backend.runtime.executors.tool_execution_port import (
    ToolExecutionPort,
)


class ToolExecutor:
    """
    Runtime tool-call consumer.

    Responsibility:
        - resolve one tool request
        - attach current workspace scope
        - delegate through ToolExecutionPort
        - propagate unsuccessful tool results

    Not Responsible:
        - tool construction
        - workspace construction
        - scheduling
        - policy implementation
    """

    VERSION = "24.0"
    name = "tool_executor"
    WORKSPACE_KEY = "workspace_root"

    RESPONSIBILITY = (
        "tool_call_execution",
        "workspace_scoped_tool_execution",
        "tool_result_failure_propagation",
    )

    def __init__(
        self,
        execution_port: ToolExecutionPort,
        resolver: ToolCallResolver | None = None,
    ) -> None:
        if execution_port is None:
            raise ValueError(
                "tool execution port required"
            )

        if not isinstance(
            execution_port,
            ToolExecutionPort,
        ):
            raise TypeError(
                "execution port must ToolExecutionPort"
            )

        self.execution_port = execution_port
        self.resolver = (
            resolver
            or ToolCallResolver()
        )
        self.execution_count = 0
        self.failure_count = 0

    async def execute(
        self,
        node: ExecutionNodeProtocol,
        context: object,
    ) -> dict[str, object]:
        self._validate_node(node)

        workspace_root = context.workspace_id

        if (
            not isinstance(workspace_root, str)
            or not workspace_root.strip()
        ):
            raise ValueError(
                "execution context workspace_id required"
            )

        request = self.resolver.resolve(
            node
        )

        request = replace(
            request,
            metadata={
                **dict(request.metadata),
                self.WORKSPACE_KEY: workspace_root,
            },
        )

        try:
            result = await self.execution_port.execute(
                request
            )
        except Exception:
            self.failure_count += 1
            raise

        if not result.success:
            self.failure_count += 1
            raise RuntimeError(
                self._failure_message(
                    request.tool_name,
                    result.error,
                )
            )

        self.execution_count += 1

        return {
            "executor": self.name,
            "status": "success",
            "tool": request.tool_name,
            "result": result,
        }

    def ready(self) -> bool:
        return (
            self.execution_port.ready()
            and self.resolver.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "execution_count": self.execution_count,
            "failure_count": self.failure_count,
            "execution_port": type(
                self.execution_port
            ).__name__,
        }

    @staticmethod
    def _validate_node(
        node: ExecutionNodeProtocol,
    ) -> None:
        if not isinstance(
            node,
            ExecutionNodeProtocol,
        ):
            raise TypeError(
                "task node must ExecutionNodeProtocol"
            )

    @staticmethod
    def _failure_message(
        tool_name: str,
        error: object,
    ) -> str:
        message = str(
            error
        ).strip()

        if message:
            return (
                f"tool execution failed: "
                f"{tool_name}: {message}"
            )

        return (
            f"tool execution failed: "
            f"{tool_name}"
        )


__all__ = [
    "ToolExecutor",
]
