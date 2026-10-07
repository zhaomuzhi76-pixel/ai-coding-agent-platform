from __future__ import annotations

from backend.core.context.kernel_context import KernelContext
from backend.core.execution import ExecutionNodeProtocol
from backend.core.tools.execution_contract import ToolExecutionResult
from backend.runtime.contracts.node_execution_result import (
    NodeExecutionResult,
)
from backend.runtime.errors.domains.execution import (
    RuntimeExecutionErrorComposition,
    RuntimeExecutionErrorConsumer,
)
from backend.runtime.execution.node_execution_service import (
    NodeExecutionService,
)
from backend.runtime.execution.runtime_node_input_materializer import (
    RuntimeNodeInputMaterializer,
)


class NodeExecutionRunner:
    """
    Runtime single-node execution boundary.

    Owns:
        - predecessor-output input materialization
        - node execution
        - context output publication
        - execution failure normalization

    Does not own:
        - scheduling
        - retry policy
        - persistence
        - transport
    """

    VERSION = "45.0"

    def __init__(
        self,
        service: NodeExecutionService,
        error_consumer: RuntimeExecutionErrorConsumer | None = None,
        input_materializer: RuntimeNodeInputMaterializer | None = None,
    ) -> None:
        if service is None:
            raise ValueError(
                "execution service required"
            )

        self.service = service
        self.input_materializer = (
            input_materializer
            if input_materializer is not None
            else RuntimeNodeInputMaterializer()
        )
        self.error_consumer = (
            error_consumer
            if error_consumer is not None
            else RuntimeExecutionErrorComposition().create()
        )

        if not isinstance(
            self.input_materializer,
            RuntimeNodeInputMaterializer,
        ):
            raise TypeError(
                "input materializer required"
            )

        if not isinstance(
            self.error_consumer,
            RuntimeExecutionErrorConsumer,
        ):
            raise TypeError(
                "execution error consumer required"
            )

    async def run(
        self,
        node: ExecutionNodeProtocol,
        context: KernelContext,
    ) -> NodeExecutionResult:
        if not isinstance(
            node,
            ExecutionNodeProtocol,
        ):
            raise TypeError(
                "node must ExecutionNodeProtocol"
            )

        if context is None:
            raise ValueError(
                "context required"
            )

        print(
            f"[runner-enter] node_id={node.node_id} "
            f"executor_type={node.executor_type!r} "
            f"params_keys={list(node.parameters.keys())}",
            flush=True,
        )

        try:
            executable = self.input_materializer.materialize(
                node,
                context,
            )
            print(
                f"[runner-materialized] "
                f"params_keys={list(executable.parameters.keys())}",
                flush=True,
            )

            output = await self.service.execute(
                executable,
                context,
            )
            print(
                f"[runner-executed] output_type={type(output).__name__}",
                flush=True,
            )

            context.set_output(
                executable.node_id,
                self._context_output(output),
            )

            return NodeExecutionResult.succeeded(
                executable.node_id,
                output,
            )

        except Exception as error:
            # ★ 详细诊断：把异常暴露到终端
            import traceback as _tb
            print(
                f"\n[runner-error] node_id={node.node_id} "
                f"executor_type={node.executor_type!r}\n"
                f"  {type(error).__name__}: {error}",
                flush=True,
            )
            _tb.print_exc()

            normalized = self.error_consumer.consume(
                error,
                operation="node.execute",
                metadata={
                    "node_id": node.node_id,
                    "executor_type": node.executor_type,
                },
            )

            return NodeExecutionResult.failed(
                node.node_id,
                normalized,
            )

    @classmethod
    def _context_output(
        cls,
        output: object,
    ) -> object:
        if isinstance(
            output,
            ToolExecutionResult,
        ):
            if not output.success:
                raise RuntimeError(
                    "tool execution failed: "
                    f"{output.error or output.tool_name}"
                )
            return output.output

        if isinstance(output, dict):
            result = output.get("result")

            if isinstance(
                result,
                ToolExecutionResult,
            ):
                if not result.success:
                    raise RuntimeError(
                        "tool execution failed: "
                        f"{result.error or result.tool_name}"
                    )
                return result.output

        return output

    def ready(
        self,
    ) -> bool:
        return (
            self.service.ready()
            and self.input_materializer.ready()
            and self.error_consumer.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "input_materializer": (
                self.input_materializer.dump()
            ),
            "error_consumer": self.error_consumer.dump(),
        }


__all__ = [
    "NodeExecutionRunner",
]
