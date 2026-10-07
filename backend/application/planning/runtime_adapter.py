from __future__ import annotations

from collections.abc import Callable

from backend.application.planning.runtime_adapter_contract import (
    PlanningRuntimeAdapterProtocol,
)
from backend.core.context.context_protocol import (
    ContextProtocol,
)
from backend.core.contracts.value import (
    CoreValue,
)
from backend.core.execution.runtime_execution_input import (
    RuntimeExecutionInput,
)
from backend.core.execution.runtime_execution_step import (
    RuntimeExecutionStep,
)
from backend.core.planning.contracts import (
    PlanningResult,
)
from backend.core.planning.step_protocol import (
    PlanningStepProtocol,
)


class PlanningRuntimeAdapter(
    PlanningRuntimeAdapterProtocol,
):
    """
    Translate canonical planning output into runtime execution input.
    """

    VERSION = "2.0"

    RESPONSIBILITY = (
        "planning_to_runtime_translation",
    )

    def adapt(
        self,
        result: PlanningResult,
        context: ContextProtocol,
        stream_callback: Callable[..., CoreValue] | None = None,
    ) -> RuntimeExecutionInput:
        self._validate(
            result,
            context,
        )

        print(f"[DIAG-ADAPT] planning steps count={len(result.steps)}", flush=True)
        for _s in result.steps:
            print(f"[DIAG-ADAPT]   step node_id={_s.node_id} executor_type={_s.executor_type!r}", flush=True)

        steps = [
            self._translate_step(step)
            for step in result.steps
        ]

        if not steps:
            raise ValueError(
                "planning result must contain steps"
            )

        return RuntimeExecutionInput(
            steps=steps,
            context=context,
            stream_callback=stream_callback,
        )

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
        }

    @staticmethod
    def _translate_step(
        step: PlanningStepProtocol,
    ) -> RuntimeExecutionStep:
        if not isinstance(
            step,
            PlanningStepProtocol,
        ):
            raise TypeError(
                "planning step must implement "
                "PlanningStepProtocol"
            )

        return RuntimeExecutionStep(
            node_id=step.node_id,
            executor_type=step.executor_type,
            node_type=(
                getattr(
                    step,
                    "node_type",
                    step.executor_type,
                )
            ),
            description=step.description,
            depends_on=list(
                step.depends_on
            ),
            parameters=dict(
                step.parameters
            ),
            metadata=dict(
                getattr(
                    step,
                    "metadata",
                    {},
                )
            ),
        )

    @staticmethod
    def _validate(
        result: PlanningResult,
        context: ContextProtocol,
    ) -> None:
        if not isinstance(
            result,
            PlanningResult,
        ):
            raise TypeError(
                "result must PlanningResult"
            )

        if not result.ready():
            raise ValueError(
                "planning result not ready"
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
    "PlanningRuntimeAdapter",
]
