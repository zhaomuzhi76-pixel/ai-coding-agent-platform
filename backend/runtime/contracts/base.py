from __future__ import annotations


from typing import Protocol, runtime_checkable


from backend.core.protocols.ready import (
    ReadyProtocol,
)

from backend.core.protocols.dumpable import (
    DumpableProtocol,
)



@runtime_checkable
class RuntimeComponentProtocol(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Runtime component boundary.


    Responsibility:

        - runtime identity boundary
        - runtime readiness
        - runtime snapshot


    Not Responsible:

        - execution
        - scheduling
        - persistence
    """



    @property
    def runtime_name(
        self,
    ) -> str:
        ...



__all__ = [
    "RuntimeComponentProtocol",
]
