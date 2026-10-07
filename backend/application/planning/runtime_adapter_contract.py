from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from backend.core.context.context_protocol import (
    ContextProtocol,
)
from backend.core.execution.runtime_execution_input import (
    RuntimeExecutionInput,
)
from backend.core.planning.contracts import PlanningResult
from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol


@runtime_checkable
class PlanningRuntimeAdapterProtocol(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Application planning-to-runtime translation contract.

    Owns only the stable adapter boundary.
    """

    def adapt(
        self,
        result: PlanningResult,
        context: ContextProtocol,
        stream_callback: Callable[..., object] | None = None,
    ) -> RuntimeExecutionInput:
        ...


__all__ = [
    "PlanningRuntimeAdapterProtocol",
]
