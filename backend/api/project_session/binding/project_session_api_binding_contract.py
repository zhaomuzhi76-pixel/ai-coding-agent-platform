from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.api.project_session.project_session_api import (
    ProjectSessionAPI,
)
from backend.api.project_session.project_session_api_router import (
    ProjectSessionAPIRouter,
)
from backend.application.project_session.project_session_adapter_contract import (
    ProjectSessionApplicationAdapterContract,
)
from backend.application.runtime_submission_contract import (
    ApplicationRuntimeSubmissionProtocol,
)
from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol


@runtime_checkable
class ProjectSessionAPIBindingContract(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Canonical API-to-application project-session binding.

    Owns:
        - application contract consumption
        - API facade construction
        - API router construction

    Does not own:
        - application concrete construction
        - project/session business logic
        - registry storage
        - lifecycle state
        - runtime construction
        - workspace construction
        - transport business semantics
    """

    def build(
        self,
    ) -> dict[str, object]:
        ...

    def api(
        self,
    ) -> ProjectSessionAPI:
        ...

    def router(
        self,
    ) -> ProjectSessionAPIRouter:
        ...

    def adapter(
        self,
    ) -> ProjectSessionApplicationAdapterContract:
        ...

    def runtime_submission(
        self,
    ) -> ApplicationRuntimeSubmissionProtocol:
        ...

    def close(
        self,
    ) -> None:
        ...
