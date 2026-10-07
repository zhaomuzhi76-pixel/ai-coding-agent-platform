from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol


@runtime_checkable
class ProjectSessionAPIServerRegistrationContract(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    FastAPI server registration contract.

    Owns:
        - construction of the upper project-session API graph
        - router registration
        - router unregistration
        - server-state projection

    Does not own:
        - project/session business logic
        - registry implementation
        - lifecycle implementation
        - runtime implementation
        - transport business rules
    """

    def register(
        self,
        app: object,
        startup: object,
    ) -> object:
        ...

    def registered(
        self,
    ) -> bool:
        ...

    def unregister(
        self,
        app: object,
    ) -> None:
        ...


__all__ = [
    "ProjectSessionAPIServerRegistrationContract",
]
