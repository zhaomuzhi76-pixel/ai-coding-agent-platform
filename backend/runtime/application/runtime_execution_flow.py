from __future__ import annotations

from backend.runtime.application.runtime_execution_plan_guard import (
    RuntimeExecutionPlanGuard,
)
from backend.runtime.application.runtime_execution_request_handler import (
    RuntimeExecutionRequestHandler,
)
from backend.runtime.application.runtime_execution_result_handler import (
    RuntimeExecutionResultHandler,
)
from backend.runtime.contracts.execution import (
    RuntimeExecutionFlowProtocol,
    RuntimeExecutionPlanGuardProtocol,
    RuntimeExecutionProtocol,
    RuntimeExecutionResultHandlerProtocol,
    RuntimeGraphBuilderProtocol,
)


class RuntimeExecutionFlow(
    RuntimeExecutionFlowProtocol,
):
    """
    Runtime execution orchestration boundary.

    Responsibility:
        - coordinate execution stages

    Not Responsible:
        - validation
        - preparation
        - graph construction
        - executor implementation
        - result processing
    """

    VERSION = "9.3"

    def __init__(
        self,
        *,
        request_handler: RuntimeExecutionRequestHandler,
        graph_builder: RuntimeGraphBuilderProtocol,
        plan_guard: RuntimeExecutionPlanGuardProtocol,
        executor: RuntimeExecutionProtocol,
        result_handler: RuntimeExecutionResultHandlerProtocol,
    ) -> None:
        if request_handler is None:
            raise ValueError(
                "request handler required"
            )

        if graph_builder is None:
            raise ValueError(
                "graph builder required"
            )

        if not isinstance(
            graph_builder,
            RuntimeGraphBuilderProtocol,
        ):
            raise TypeError(
                "graph builder must implement "
                "RuntimeGraphBuilderProtocol"
            )

        if plan_guard is None:
            raise ValueError(
                "plan guard required"
            )

        if not isinstance(
            plan_guard,
            RuntimeExecutionPlanGuardProtocol,
        ):
            raise TypeError(
                "plan guard must implement "
                "RuntimeExecutionPlanGuardProtocol"
            )

        if executor is None:
            raise ValueError(
                "runtime execution engine required"
            )

        if not isinstance(
            executor,
            RuntimeExecutionProtocol,
        ):
            raise TypeError(
                "executor must implement "
                "RuntimeExecutionProtocol"
            )

        if result_handler is None:
            raise ValueError(
                "result handler required"
            )

        if not isinstance(
            result_handler,
            RuntimeExecutionResultHandlerProtocol,
        ):
            raise TypeError(
                "result handler must implement "
                "RuntimeExecutionResultHandlerProtocol"
            )

        self.request_handler = request_handler
        self.graph_builder = graph_builder
        self.plan_guard = plan_guard
        self.executor = executor
        self.result_handler = result_handler

    async def execute(
        self,
        *,
        request,
        context,
        stream_callback=None,
    ) -> list[object]:
        print(f"[DIAG-FLOW] enter request={getattr(request, 'message', '?')!r}", flush=True)

        execution_input = await (
            self.request_handler.prepare(
                request=request,
                context=context,
                stream_callback=stream_callback,
            )
        )

        print(f"[DIAG-FLOW] runtime steps count={len(execution_input.steps)}", flush=True)
        for _st in execution_input.steps:
            print(f"[DIAG-FLOW]   runtime node_id={_st.node_id} executor_type={_st.executor_type!r}", flush=True)

        plan = self.graph_builder.build(
            execution_input.steps,
        )

        plan = self.plan_guard.validate(
            plan
        )

        print("[DIAG-FLOW] calling executor.execute", flush=True)
        outputs = await self.executor.execute(
            graph=plan.graph,
            execution_input=execution_input,
            context=context,
            stream_callback=stream_callback,
        )

        print(f"[DIAG-FLOW] executor returned outputs={len(outputs)}", flush=True)
        return self.result_handler.handle(
            outputs
        )

    def ready(
        self,
    ) -> bool:
        return all(
            (
                self.request_handler.ready(),
                self.graph_builder.ready(),
                self.plan_guard.ready(),
                self.executor.ready(),
                self.result_handler.ready(),
            )
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "RuntimeExecutionFlow",
]
