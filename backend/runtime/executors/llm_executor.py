from __future__ import annotations

from backend.core.agent.agent_request import AgentRequest
from backend.core.context.kernel_context import KernelContext
from backend.core.execution.llm_execution_contract import LLMExecutionProviderProtocol
from backend.core.execution import ExecutionNodeProtocol


class LLMExecutor:
    """Runtime LLM execution executor."""

    VERSION = "18.0"
    name = "llm"
    REQUEST_CONTEXT_KEY = "agent_request"
    REQUEST_METADATA_KEY = "agent_request_object"

    def __init__(self, provider: LLMExecutionProviderProtocol) -> None:
        if provider is None:
            raise ValueError("llm provider required")
        if not isinstance(provider, LLMExecutionProviderProtocol):
            raise TypeError("llm provider contract required")
        self.provider = provider
        self.execution_count = 0
        self.failure_count = 0

    async def execute(self, node: ExecutionNodeProtocol, context: KernelContext) -> dict[str, object]:
        self._validate_node(node)
        self.execution_count += 1
        request = self._request(context)
        try:
            response = await self.provider.chat(
                provider=request.provider,
                model=request.model,
                messages=[{"role": "user", "content": self._message(node)}],
            )
            return {"executor": self.name, "status": "success", "content": response}
        except Exception:
            self.failure_count += 1
            raise

    @staticmethod
    def _validate_node(node: ExecutionNodeProtocol) -> None:
        if not isinstance(node, ExecutionNodeProtocol):
            raise TypeError("node must ExecutionNodeProtocol")

    @classmethod
    def _request(cls, context: KernelContext) -> AgentRequest:
        if context is None:
            raise ValueError("runtime context required")
        request = context.metadata.get(
            cls.REQUEST_METADATA_KEY,
            None,
        )
        if isinstance(request, AgentRequest):
            if not request.ready():
                raise ValueError("llm request not ready")
            return request

        snapshot = context.get(
            cls.REQUEST_CONTEXT_KEY,
            None,
        )
        if isinstance(snapshot, AgentRequest):
            if not snapshot.ready():
                raise ValueError("llm request not ready")
            return snapshot
        if snapshot is not None:
            raise TypeError(
                "llm request context contains a serialized request snapshot; "
                "canonical AgentRequest object unavailable"
            )
        raise TypeError("llm request must AgentRequest")

    @staticmethod
    def _message(node: ExecutionNodeProtocol) -> str:
        parameters = node.parameters
        message = parameters.get("message")
        if isinstance(message, str) and message.strip():
            return message
        tool_call = parameters.get("tool_call")
        if isinstance(tool_call, dict):
            arguments = tool_call.get("arguments")
            if isinstance(arguments, dict):
                message = arguments.get("message")
                if isinstance(message, str) and message.strip():
                    return message
        return node.description

    def ready(self) -> bool:
        return self.provider.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.VERSION,
            "ready": self.ready(),
            "execution_count": self.execution_count,
            "failure_count": self.failure_count,
            "request_context_key": self.REQUEST_CONTEXT_KEY,
            "request_metadata_key": self.REQUEST_METADATA_KEY,
        }


__all__ = ["LLMExecutor"]
