from __future__ import annotations

from dataclasses import replace

from backend.core.context.kernel_context import KernelContext
from backend.core.execution import ExecutionNodeProtocol
from backend.core.execution.runtime_execution_step import (
    RuntimeExecutionStep,
)
from backend.core.tools.execution_contract import (
    ToolExecutionResult,
)


class RuntimeNodeInputMaterializer:
    """
    Runtime source_step input materializer.

    Owns:
        - resolving predecessor output data
        - extracting canonical tool output payload
        - injecting resolved content into a cloned node

    Does not own:
        - execution
        - scheduling
        - lifecycle state
        - result persistence
    """

    VERSION = "1.1"

    def materialize(
        self,
        node: ExecutionNodeProtocol,
        context: KernelContext,
    ) -> ExecutionNodeProtocol:
        if not isinstance(
            node,
            ExecutionNodeProtocol,
        ):
            raise TypeError(
                "node must ExecutionNodeProtocol"
            )

        if context is None:
            raise ValueError("context required")

        call = node.parameters.get("tool_call")
        if not isinstance(call, dict):
            return node

        arguments = call.get("arguments")
        if not isinstance(arguments, dict):
            return node

        source_step = arguments.get("source_step")
        if (
            not isinstance(source_step, str)
            or not source_step.strip()
        ):
            return node

        output = context.get_output(
            source_step.strip()
        )
        if output is None:
            raise KeyError(
                "source step output unavailable: "
                f"{source_step}"
            )

        content = self._content(output)

        if not isinstance(content, str):
            raise TypeError(
                "source step output must provide text content: "
                f"{source_step}"
            )

        next_arguments = dict(arguments)
        next_arguments["content"] = content

        next_call = dict(call)
        next_call["arguments"] = next_arguments

        next_parameters = dict(node.parameters)
        next_parameters["tool_call"] = next_call

        if not isinstance(
            node,
            RuntimeExecutionStep,
        ):
            raise TypeError(
                "runtime node must RuntimeExecutionStep"
            )

        return replace(
            node,
            parameters=next_parameters,
        )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }

    @classmethod
    def _content(cls, value: object) -> object:
        if isinstance(value, str):
            return value

        if isinstance(value, ToolExecutionResult):
            if not value.success:
                raise RuntimeError(
                    "source step tool execution failed: "
                    f"{value.error or value.tool_name}"
                )
            return cls._content(value.output)

        if isinstance(value, dict):
            for key in (
                "content",
                "output",
                "result",
                "replacement",
                "value",
            ):
                if key in value:
                    return cls._content(value[key])

        return value


__all__ = [
    "RuntimeNodeInputMaterializer",
]
