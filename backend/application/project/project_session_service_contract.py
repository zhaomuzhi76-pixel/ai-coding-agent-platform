from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol


@runtime_checkable
class ApplicationProjectSessionServiceContract(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Application-facing project-session service port.

    Owns only the session information required by
    application project-removal coordination.

    Does not expose workspace/session implementation details.
    """

    def project_sessions(
        self,
        project_id: str,
    ) -> Any:
        ...


__all__ = [
    "ApplicationProjectSessionServiceContract",
]
