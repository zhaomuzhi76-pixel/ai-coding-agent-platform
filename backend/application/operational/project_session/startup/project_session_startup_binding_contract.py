from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol


@runtime_checkable
class ProjectSessionStartupBindingContract(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Startup binding contract for the project-session runtime stack.

    Owns:
        - startup-time runtime-submission binding
        - startup readiness projection
        - teardown

    Does not own:
        - project/session construction
        - lifecycle implementation
        - runtime construction
        - execution implementation
        - transport
        - parallel execution bridge
    """

    def start(
        self,
        runtime_submission: object,
    ) -> object:
        ...

    def stop(
        self,
    ) -> None:
        ...


__all__ = [
    "ProjectSessionStartupBindingContract",
]
