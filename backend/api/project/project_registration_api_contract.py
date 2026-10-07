from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.application.project.project_result_contract import (
    ApplicationProjectResultContract,
)
from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol


@runtime_checkable
class ProjectRegistrationAPIContract(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    HTTP-facing project-registration contract.

    The API contract exposes an application project result projection
    and does not depend on workspace implementation types.
    """

    def register(
        self,
        payload: dict[str, object],
    ) -> ApplicationProjectResultContract:
        ...

    def get(
        self,
        project_id: str,
    ) -> ApplicationProjectResultContract:
        ...

    def remove(
        self,
        project_id: str,
    ) -> ApplicationProjectResultContract:
        ...
