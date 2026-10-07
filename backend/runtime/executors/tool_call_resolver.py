from __future__ import annotations

from backend.core.tools.execution_contract import (
    ToolExecutionRequest,
)
from backend.core.execution import (
    ExecutionNodeProtocol,
)


class ToolCallResolver:
    """
    Resolve a runtime node tool call into the Core-owned
    canonical ToolExecutionRequest.
    """

    VERSION = "5.0"

    def resolve(
        self,
        node: ExecutionNodeProtocol,
    ) -> ToolExecutionRequest:
        if not isinstance(
            node,
            ExecutionNodeProtocol,
        ):
            raise TypeError(
                "node must ExecutionNodeProtocol"
            )

        call = node.parameters.get(
            "tool_call"
        )

        if not isinstance(
            call,
            dict,
        ):
            raise ValueError(
                "tool_call missing"
            )

        name = call.get("name")

        if not isinstance(
            name,
            str,
        ) or not name.strip():
            raise ValueError(
                "tool name required"
            )

        arguments = call.get(
            "arguments",
            {},
        )

        if not isinstance(
            arguments,
            dict,
        ):
            raise TypeError(
                "tool arguments must dict"
            )

        request = ToolExecutionRequest(
            tool_name=name.strip(),
            arguments=dict(arguments),
            role="runtime",
        )

        if not request.ready():
            raise RuntimeError(
                "resolved tool request not ready"
            )

        return request

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ToolCallResolver",
]
