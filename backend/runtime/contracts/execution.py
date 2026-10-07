from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from backend.core.context.context_protocol import (
    ContextProtocol,
)
from backend.core.execution.runtime_execution_input import (
    RuntimeExecutionInput,
)
from backend.runtime.contracts.node_execution_result import (
    NodeExecutionResult,
)
from backend.runtime.contracts.runtime_execution_plan import (
    RuntimeExecutionPlan,
)
from backend.core.execution.runtime_execution_step import (
    RuntimeExecutionStep,
)
from backend.runtime.contracts.runtime_graph import (
    RuntimeGraph,
)


@runtime_checkable
class RuntimeExecutionPreparerProtocol(
    Protocol,
):
    async def prepare(
        self,
        request,
        context,
        stream_callback=None,
    ) -> RuntimeExecutionInput:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, object]:
        ...


from backend.core.execution.execution_flow_protocol import (
    ExecutionFlowProtocol,
)

RuntimeExecutionFlowProtocol = ExecutionFlowProtocol


@runtime_checkable
class RuntimeExecutionProtocol(
    Protocol,
):
    async def execute(
        self,
        *,
        graph: RuntimeGraph,
        execution_input: RuntimeExecutionInput,
        context: ContextProtocol,
        stream_callback: Callable[..., object] | None = None,
    ) -> list[object]:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, object]:
        ...


@runtime_checkable
class RuntimeGraphBuilderProtocol(
    Protocol,
):
    def build(
        self,
        steps: list[RuntimeExecutionStep],
    ) -> RuntimeExecutionPlan:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, object]:
        ...


@runtime_checkable
class RuntimeExecutionPlanGuardProtocol(
    Protocol,
):
    def validate(
        self,
        plan: RuntimeExecutionPlan,
    ) -> RuntimeExecutionPlan:
        ...

    def ready(
        self,
    ) -> bool:
        ...


@runtime_checkable
class RuntimeExecutionResultHandlerProtocol(
    Protocol,
):
    def handle(
        self,
        outputs: list[object],
    ) -> list[object]:
        ...

    def ready(
        self,
    ) -> bool:
        ...


__all__ = [
    "NodeExecutionResult",
    "RuntimeExecutionFlowProtocol",
    "RuntimeExecutionInput",
    "RuntimeExecutionPlan",
    "RuntimeExecutionPlanGuardProtocol",
    "RuntimeExecutionPreparerProtocol",
    "RuntimeExecutionProtocol",
    "RuntimeExecutionResultHandlerProtocol",
    "RuntimeExecutionStep",
    "RuntimeGraphBuilderProtocol",
]
