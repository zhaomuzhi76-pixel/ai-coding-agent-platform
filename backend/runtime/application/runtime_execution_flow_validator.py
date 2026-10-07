from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.agent.agent_request import AgentRequest
from backend.core.context.kernel_context import KernelContext
from backend.runtime.contracts.execution import RuntimeExecutionInput


@runtime_checkable
class GraphValidationProtocol(Protocol):
    def validate_graph(
        self,
    ) -> bool:
        ...


class RuntimeExecutionFlowValidator:
    """
    Runtime execution flow validation boundary.

    Responsibility:
        - validate request/context boundary
        - validate prepared execution input
        - validate graph boundary
        - validate execution outputs

    Not Responsible:
        - graph construction
        - execution
        - scheduling
        - result processing
        - persistence
    """

    VERSION = "3.2"

    RESPONSIBILITY = (
        "runtime_execution_flow_validation",
    )

    def validate_request(
        self,
        request: AgentRequest,
        context: KernelContext,
    ) -> None:
        if request is None:
            raise ValueError(
                "AgentRequest required"
            )

        if not isinstance(
            request,
            AgentRequest,
        ):
            raise TypeError(
                "request must be AgentRequest"
            )

        if not request.ready():
            raise ValueError(
                "AgentRequest not ready"
            )

        if context is None:
            raise ValueError(
                "KernelContext required"
            )

        if not isinstance(
            context,
            KernelContext,
        ):
            raise TypeError(
                "context must implement KernelContext"
            )

    def validate_input(
        self,
        runtime_input: RuntimeExecutionInput,
    ) -> None:
        if not isinstance(
            runtime_input,
            RuntimeExecutionInput,
        ):
            raise TypeError(
                "RuntimeExecutionInput required"
            )

        if runtime_input.context is None:
            raise ValueError(
                "RuntimeExecutionInput context required"
            )

        if not isinstance(
            runtime_input.steps,
            list,
        ):
            raise TypeError(
                "RuntimeExecutionInput steps must list"
            )

    def validate_graph(
        self,
        graph: GraphValidationProtocol,
    ) -> None:
        if not isinstance(
            graph,
            GraphValidationProtocol,
        ):
            raise TypeError(
                "graph must implement validation protocol"
            )

        if not graph.validate_graph():
            raise ValueError(
                "runtime graph validation failed"
            )

    def validate_outputs(
        self,
        outputs: list[object],
    ) -> None:
        if not isinstance(
            outputs,
            list,
        ):
            raise TypeError(
                "execution outputs must list"
            )

    def validate(
        self,
        *,
        request: AgentRequest | None = None,
        context: KernelContext | None = None,
        runtime_input: RuntimeExecutionInput | None = None,
        graph: GraphValidationProtocol | None = None,
        outputs: list[object] | None = None,
    ) -> None:
        """
        Unified validation facade.

        Exactly one validation target may be supplied.
        """
        supplied = sum(
            value is not None
            for value in (
                request,
                runtime_input,
                graph,
                outputs,
            )
        )

        if supplied != 1:
            raise ValueError(
                "exactly one validation target required"
            )

        if request is not None:
            self.validate_request(
                request,
                context,
            )
            return

        if runtime_input is not None:
            self.validate_input(
                runtime_input,
            )
            return

        if graph is not None:
            self.validate_graph(
                graph,
            )
            return

        self.validate_outputs(
            outputs,
        )

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
        }


__all__ = [
    "GraphValidationProtocol",
    "RuntimeExecutionFlowValidator",
]
