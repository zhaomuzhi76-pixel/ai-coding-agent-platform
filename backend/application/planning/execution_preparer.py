from __future__ import annotations

from backend.core.contracts.value import CoreValue

from collections.abc import Callable

from backend.application.planning.execution_preparer_contract import (
    PlanningExecutionPreparerProtocol,
)
from backend.application.planning.runtime_adapter import (
    PlanningRuntimeAdapter,
)
from backend.application.planning.service import (
    PlanningApplicationService,
)
from backend.core.agent.agent_request import (
    AgentRequest,
)
from backend.core.context.context_protocol import (
    ContextProtocol,
)
from backend.core.execution.runtime_execution_input import (
    RuntimeExecutionInput,
)
from backend.core.planning.contracts import (
    PlanningRequest,
)

from backend.application.planning.workspace_path_normalizer import (
    normalize_workspace_path,
)


class PlanningExecutionPreparer(
    PlanningExecutionPreparerProtocol,
):
    """
    Planning-owned runtime execution preparation boundary.

    Responsibility:
        - translate AgentRequest into PlanningRequest
        - invoke application planning service
        - adapt PlanningResult into RuntimeExecutionInput

    Does not own:
        - planner implementation
        - runtime execution
        - runtime provider construction
        - executor construction
        - result processing
        - persistence
    """

    VERSION = "2.0"

    RESPONSIBILITY = (
        "planning_execution_preparation",
    )

    def __init__(
        self,
        planning_service: PlanningApplicationService,
        adapter: PlanningRuntimeAdapter,
    ) -> None:
        if planning_service is None:
            raise ValueError(
                "planning service required"
            )

        if not isinstance(
            planning_service,
            PlanningApplicationService,
        ):
            raise TypeError(
                "planning service must "
                "PlanningApplicationService"
            )

        if adapter is None:
            raise ValueError(
                "planning runtime adapter required"
            )

        if not isinstance(
            adapter,
            PlanningRuntimeAdapter,
        ):
            raise TypeError(
                "adapter must PlanningRuntimeAdapter"
            )

        self.planning_service = planning_service
        self.adapter = adapter

    async def prepare(
        self,
        request: AgentRequest,
        context: ContextProtocol,
        stream_callback: Callable[..., object] | None = None,
    ) -> RuntimeExecutionInput:
        self._validate(
            request,
            context,
        )

        print(f"[DIAG-PREPARE] message={request.message!r} workspace={request.workspace!r} model={request.model!r}", flush=True)

        normalized_workspace = normalize_workspace_path(
            request.workspace
        )
        print(
            f"[DIAG-NORM] workspace in={request.workspace!r} out={normalized_workspace!r}",
            flush=True,
        )

        planning_request = PlanningRequest(
            message=request.message,
            workspace=normalized_workspace,
            model=request.model,
            metadata={
                "session_id": request.session_id,
                "user_id": request.user_id,
                **dict(request.metadata),
            },
        )

        result = await self.planning_service.plan(
            planning_request
        )

        return self.adapter.adapt(
            result=result,
            context=context,
            stream_callback=stream_callback,
        )

    def ready(
        self,
    ) -> bool:
        return (
            self.planning_service.ready()
            and self.adapter.ready()
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "planning_service": type(
                self.planning_service
            ).__name__,
            "adapter": type(
                self.adapter
            ).__name__,
        }

    @staticmethod
    def _validate(
        request: AgentRequest,
        context: ContextProtocol,
    ) -> None:
        if not isinstance(
            request,
            AgentRequest,
        ):
            raise TypeError(
                "request must AgentRequest"
            )

        if not request.ready():
            raise ValueError(
                "agent request not ready"
            )

        if not isinstance(
            context,
            ContextProtocol,
        ):
            raise TypeError(
                "context must implement ContextProtocol"
            )

        if not context.ready():
            raise RuntimeError(
                "runtime context not ready"
            )


__all__ = [
    "PlanningExecutionPreparer",
]
