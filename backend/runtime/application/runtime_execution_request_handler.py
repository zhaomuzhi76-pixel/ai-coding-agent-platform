from __future__ import annotations

from backend.core.agent.agent_request import AgentRequest
from backend.core.context.kernel_context import KernelContext
from backend.runtime.application.runtime_execution_flow_validator import (
    RuntimeExecutionFlowValidator,
)
from backend.runtime.contracts.execution import (
    RuntimeExecutionPreparerProtocol,
)


class RuntimeExecutionRequestHandler:
    """
    Prepare runtime execution request.

    Responsibility:
        - validate request
        - bind serializable request snapshot
        - bind canonical request object for executor use
        - prepare execution input
    """

    VERSION = "1.3"
    REQUEST_CONTEXT_KEY = "agent_request"
    REQUEST_METADATA_KEY = "agent_request_object"

    def __init__(
        self,
        *,
        validator: RuntimeExecutionFlowValidator,
        preparer: RuntimeExecutionPreparerProtocol,
    ) -> None:
        if validator is None:
            raise ValueError("validator required")
        if preparer is None:
            raise ValueError("preparer required")
        if not isinstance(
            preparer,
            RuntimeExecutionPreparerProtocol,
        ):
            raise TypeError(
                "preparer must implement "
                "RuntimeExecutionPreparerProtocol"
            )

        self.validator = validator
        self.preparer = preparer

    async def prepare(
        self,
        *,
        request: AgentRequest,
        context: KernelContext,
        stream_callback=None,
    ):
        self.validator.validate_request(
            request,
            context,
        )
        self._bind_request(
            context,
            request,
        )

        result = await self.preparer.prepare(
            request=request,
            context=context,
            stream_callback=stream_callback,
        )
        self.validator.validate_input(result)
        return result

    def ready(self) -> bool:
        return (
            self.validator.ready()
            and self.preparer.ready()
        )

    @classmethod
    def request_key(cls) -> str:
        return cls.REQUEST_CONTEXT_KEY

    @classmethod
    def request_object_key(cls) -> str:
        return cls.REQUEST_METADATA_KEY

    @classmethod
    def _bind_request(
        cls,
        context: KernelContext,
        request: AgentRequest,
    ) -> None:
        cls._validate_request(request)
        if not isinstance(context, KernelContext):
            raise TypeError("context must KernelContext")

        snapshot = request.dump()

        if not isinstance(snapshot, dict):
            raise TypeError(
                "agent request dump must be CoreValue mapping"
            )

        context.set(
            cls.REQUEST_CONTEXT_KEY,
            snapshot,
        )
        context.metadata.set(
            cls.REQUEST_METADATA_KEY,
            request,
        )

        bound_snapshot = context.get(
            cls.REQUEST_CONTEXT_KEY,
        )
        bound_request = context.metadata.get(
            cls.REQUEST_METADATA_KEY,
        )

        if bound_snapshot != snapshot:
            raise RuntimeError(
                "runtime request snapshot binding failed"
            )

        if bound_request is not request:
            raise RuntimeError(
                "runtime request object binding failed"
            )

    @staticmethod
    def _validate_request(
        request: AgentRequest,
    ) -> None:
        if not isinstance(
            request,
            AgentRequest,
        ):
            raise TypeError(
                "request must AgentRequest"
            )
        if not request.ready():
            raise ValueError("request not ready")


__all__ = [
    "RuntimeExecutionRequestHandler",
]
