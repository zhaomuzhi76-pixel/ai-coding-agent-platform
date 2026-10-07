from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol


@runtime_checkable
class ProjectRegistrationServerRegistrationContract(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    FastAPI server-registration contract for project registration.

    Owns:
        - registration of the frozen project-registration router
        - unregistration of the owned routes
        - registration-state projection

    Does not own:
        - project registry construction
        - project construction
        - project business logic
        - session business logic
        - runtime construction
        - application lifecycle policy
    """

    def register(
        self,
        app: object,
        startup: object,
    ) -> object:
        ...

    def unregister(
        self,
        app: object,
    ) -> None:
        ...

    def registered(
        self,
    ) -> bool:
        ...


__all__ = [
    "ProjectRegistrationServerRegistrationContract",
]
