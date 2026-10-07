from __future__ import annotations

from backend.core.context.kernel_context import (
    KernelContext,
)
from backend.core.agent.agent_request import (
    AgentRequest,
)
from backend.core.context.context_metadata import (
    ContextMetadata,
)
from backend.core.context.execution_context_storage import (
    ExecutionContextStorage,
)
from backend.core.context.execution_output_store import (
    ExecutionOutputStore,
)
from backend.core.context.execution_variable_store import (
    ExecutionVariableStore,
)
from backend.core.context.runtime_context import (
    RuntimeContext,
)
from backend.core.execution.execution_lifecycle_state import (
    ExecutionLifecycleState,
)


class ApplicationContextFactory:
    """
    Application execution context construction boundary.

    Owns:
        - construct canonical context dependencies
        - construct Core-owned execution lifecycle state
        - inject request scope into canonical context
        - assemble KernelContext

    Does not own:
        - agent execution
        - runtime execution
        - lifecycle transition control
        - persistence
        - result serialization
        - transport
    """

    VERSION = "3.0"

    RESPONSIBILITY = (
        "application_context_construction",
        "core_execution_lifecycle_state_construction",
        "application_context_identity_injection",
    )

    def create(
        self,
        request: AgentRequest,
        session_id: str,
    ) -> KernelContext:
        self._validate(
            request,
            session_id,
        )

        storage = ExecutionContextStorage(
            variable_store=ExecutionVariableStore(),
            output_store=ExecutionOutputStore(),
        )

        metadata = ContextMetadata()

        runtime_context = RuntimeContext(
            storage=storage,
            metadata=metadata,
            request_id=session_id,
            workspace_id=request.workspace,
            user_id=request.user_id or None,
        )

        if not runtime_context.ready():
            raise RuntimeError(
                "application runtime context unavailable"
            )

        lifecycle_state = ExecutionLifecycleState(
            task_id=session_id,
        )

        if not lifecycle_state.ready():
            raise RuntimeError(
                "application execution lifecycle state unavailable"
            )

        context = KernelContext.create(
            runtime_context=runtime_context,
            lifecycle_state=lifecycle_state,
            session_id=session_id,
        )

        if not context.ready():
            raise RuntimeError(
                "application kernel context unavailable"
            )

        context.set("provider", request.provider)
        context.set("model", request.model)

        return context

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
        }

    @staticmethod
    def _validate(
        request: AgentRequest,
        session_id: str,
    ) -> None:
        if not isinstance(
            request,
            AgentRequest,
        ):
            raise TypeError(
                "request must be AgentRequest"
            )

        if not isinstance(
            session_id,
            str,
        ) or not session_id.strip():
            raise ValueError(
                "session id required"
            )


__all__ = [
    "ApplicationContextFactory",
]
