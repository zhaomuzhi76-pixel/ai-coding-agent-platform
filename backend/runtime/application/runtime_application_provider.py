from __future__ import annotations

from backend.runtime.application.request_validator import (
    RuntimeRequestValidator,
)
from backend.runtime.application.result_contract import (
    RuntimeResultFactoryProtocol,
)
from backend.runtime.application.runtime_execution_flow import (
    RuntimeExecutionFlow,
)
from backend.runtime.application.runtime_execution_flow_validator import (
    RuntimeExecutionFlowValidator,
)
from backend.runtime.application.runtime_execution_plan_guard import (
    RuntimeExecutionPlanGuard,
)
from backend.runtime.application.runtime_execution_request_handler import (
    RuntimeExecutionRequestHandler,
)
from backend.runtime.application.runtime_execution_result_handler import (
    RuntimeExecutionResultHandler,
)
from backend.runtime.application.runtime_result_factory import (
    RuntimeResultFactory,
)
from backend.runtime.contracts.execution import (
    RuntimeExecutionPlanGuardProtocol,
    RuntimeExecutionPreparerProtocol,
    RuntimeExecutionProtocol,
    RuntimeExecutionResultHandlerProtocol,
    RuntimeGraphBuilderProtocol,
)
from backend.runtime.execution.runtime_graph_builder import (
    RuntimeGraphBuilder,
)


class RuntimeApplicationProvider:
    """
    Runtime execution-flow construction boundary.

    Owns:
        - runtime execution flow construction
        - runtime result-factory ownership

    Does not own:
        - Application execution facade
        - transport
        - persistence
        - session admission
    """

    VERSION = "10.0"

    def __init__(
        self,
        capability_registry,
        request_validator: RuntimeRequestValidator | None = None,
        result_factory: RuntimeResultFactoryProtocol | None = None,
    ) -> None:
        self.capability_registry = capability_registry
        self.request_validator = (
            request_validator
            or RuntimeRequestValidator()
        )
        self.result_factory = (
            result_factory
            or RuntimeResultFactory()
        )

        if not self.ready():
            raise RuntimeError(
                "runtime execution-flow provider unavailable"
            )

    def create_flow(
        self,
        *,
        preparer: RuntimeExecutionPreparerProtocol,
        executor: RuntimeExecutionProtocol,
        graph_builder: RuntimeGraphBuilderProtocol | None = None,
        plan_guard: RuntimeExecutionPlanGuardProtocol | None = None,
        result_handler: RuntimeExecutionResultHandlerProtocol | None = None,
    ) -> RuntimeExecutionFlow:
        if not preparer.ready():
            raise RuntimeError(
                "execution preparer not ready"
            )

        if not executor.ready():
            raise RuntimeError(
                "runtime executor not ready"
            )

        validator = RuntimeExecutionFlowValidator()

        return RuntimeExecutionFlow(
            request_handler=RuntimeExecutionRequestHandler(
                validator=validator,
                preparer=preparer,
            ),
            graph_builder=(
                graph_builder
                or RuntimeGraphBuilder()
            ),
            plan_guard=(
                plan_guard
                or RuntimeExecutionPlanGuard()
            ),
            executor=executor,
            result_handler=(
                result_handler
                or RuntimeExecutionResultHandler(
                    validator
                )
            ),
        )

    def create_result_factory(
        self,
    ) -> RuntimeResultFactoryProtocol:
        return self.result_factory

    def ready(self) -> bool:
        return (
            self.request_validator.ready()
            and self.result_factory.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "RuntimeApplicationProvider",
]
