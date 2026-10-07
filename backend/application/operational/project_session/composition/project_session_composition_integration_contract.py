from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol


@runtime_checkable
class ProjectSessionCompositionIntegrationContract(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Final project-session runtime-submission integration contract.

    Owns:
        - assembled runtime-submission bridge

    Does not own:
        - construction
        - lifecycle mutation
        - registry storage
        - runtime implementation
        - transport
        - parallel execution bridge
    """

    def build(
        self,
        *,
        runtime_submission: object,
    ) -> dict[str, object]:
        ...

    def runtime_submission(
        self,
    ) -> object:
        ...


__all__ = [
    "ProjectSessionCompositionIntegrationContract",
]
