from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.context.execution_output import ExecutionOutput
from backend.core.context.execution_variable import ExecutionVariable
from backend.core.context.identity_context_protocol import (
    IdentityContextProtocol,
)
from backend.core.context.context_protocol import ContextProtocol


@runtime_checkable
class ContextAccessProtocol(
    ContextProtocol,
    IdentityContextProtocol,
    Protocol,
):
    """
    Canonical Context access capability.

    Responsibility:
        - expose canonical identity values
        - expose controlled execution-variable access
        - expose controlled execution-output access
        - expose readiness and clearing through ContextProtocol

    Not Responsible:
        - storage implementation
        - persistence
        - transport
        - execution lifecycle
        - scheduling
    """

    def get_variable(
        self,
        name: str,
    ) -> ExecutionVariable | None:
        ...

    def set_variable(
        self,
        variable: ExecutionVariable,
    ) -> None:
        ...

    def remove_variable(
        self,
        name: str,
    ) -> None:
        ...

    def variable_names(
        self,
    ) -> tuple[str, ...]:
        ...

    def get_output(
        self,
        name: str,
    ) -> ExecutionOutput | None:
        ...

    def set_output(
        self,
        output: ExecutionOutput,
    ) -> None:
        ...

    def remove_output(
        self,
        name: str,
    ) -> None:
        ...

    def output_names(
        self,
    ) -> tuple[str, ...]:
        ...


__all__ = [
    "ContextAccessProtocol",
]
