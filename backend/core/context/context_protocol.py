from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.context.context_snapshot_contract import (
    ContextSnapshot,
)

from backend.core.protocols.dumpable import (
    DumpableProtocol,
)

from backend.core.protocols.ready import (
    ReadyProtocol,
)


@runtime_checkable
class ContextProtocol(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Runtime context capability contract.

    Responsibility:

        - define the minimal runtime context boundary

    Not Responsible:

        - storage
        - variables
        - outputs
        - lifecycle
        - persistence
        - scheduling
    """

    def dump(
        self,
    ) -> ContextSnapshot:
        ...


__all__ = [
    "ContextProtocol",
]
