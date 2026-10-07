from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from backend.core.contracts.value import CoreValue
from backend.core.context.kernel_context import (
    KernelContext,
)
from backend.core.execution.runtime_execution_step import (
    RuntimeExecutionStep,
)


@dataclass(frozen=True)
class RuntimeExecutionInput:
    """
    Core-owned runtime execution input contract.

    Responsibility:
        - carry prepared execution steps
        - carry canonical kernel execution context
        - carry optional stream callback

    Not Responsible:
        - planning
        - runtime execution
        - scheduling
        - persistence
    """

    steps: list[RuntimeExecutionStep]
    context: KernelContext
    stream_callback: Callable[..., CoreValue] | None = None


__all__ = [
    "RuntimeExecutionInput",
]
