from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.context.context_protocol import (
    ContextProtocol,
)
from backend.core.contracts.value import (
    CoreValue,
)
from backend.core.protocols.dumpable import (
    DumpableProtocol,
)
from backend.core.protocols.ready import (
    ReadyProtocol,
)
from backend.core.result import (
    ExecutionResult,
)


@runtime_checkable
class ExecutionNodeProtocol(
    Protocol,
):
    """
    Stable execution node contract.

    Responsibility:
        - expose node identity
        - expose dependency metadata
        - expose logical executor type
        - expose immutable execution parameters

    Not Responsible:
        - runtime state
        - execution lifecycle
        - scheduling
        - persistence
    """

    @property
    def node_id(
        self,
    ) -> str:
        ...

    @property
    def depends_on(
        self,
    ) -> list[str]:
        ...

    @property
    def executor_type(
        self,
    ) -> str:
        ...

    @property
    def parameters(
        self,
    ) -> dict[str, CoreValue]:
        ...


@runtime_checkable
class ExecutorProtocol(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Stable executor capability contract.
    """

    name: str

    async def execute(
        self,
        node: ExecutionNodeProtocol,
        context: ContextProtocol,
    ) -> object:
        ...


@runtime_checkable
class ExecutorResolverProtocol(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Stable executor resolution contract.
    """

    def resolve_executor(
        self,
        executor_type: str,
    ) -> ExecutorProtocol:
        ...


__all__ = [
    "ExecutionNodeProtocol",
    "ExecutorProtocol",
    "ExecutorResolverProtocol",
]
