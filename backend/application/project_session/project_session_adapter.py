from __future__ import annotations

from typing import Any

from backend.application.project_session.project_session_adapter_contract import (
    ProjectSessionApplicationAdapterContract,
)
from backend.workspace.project.session.contracts.project_session_contract import (
    ProjectSessionContract,
)
from backend.workspace.project.session.service.project_session_service_contract import (
    ProjectSessionServiceContract,
)


class ProjectSessionApplicationAdapter(
    ProjectSessionApplicationAdapterContract,
):
    """
    Application adapter over the frozen project-session service.

    Owns:
        - application adapter identity
        - boundary validation
        - direct delegation to ProjectSessionServiceContract

    Does not own:
        - project/session construction
        - registry storage
        - lifecycle state
        - runtime/workspace construction
        - business reimplementation
    """

    VERSION = "1.0"

    NAME = "project_session.application"

    def __init__(
        self,
        service: ProjectSessionServiceContract,
    ) -> None:
        if not isinstance(
            service,
            ProjectSessionServiceContract,
        ):
            raise TypeError(
                "service must "
                "ProjectSessionServiceContract"
            )

        if not service.ready():
            raise RuntimeError(
                "project session service not ready"
            )

        self.service = service
        self.request_count = 0

    @property
    def name(self) -> str:
        return self.NAME

    @property
    def version(self) -> str:
        return self.VERSION

    def create_session(
        self,
        project_id: str,
        session_id: str | None = None,
        workspace_id: str | None = None,
        runtime_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> ProjectSessionContract:
        result = self.service.create_session(
            project_id=project_id,
            session_id=session_id,
            workspace_id=workspace_id,
            runtime_id=runtime_id,
            metadata=metadata,
        )
        self._record(result)
        return result

    def get_session(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        result = self.service.get_session(
            session_id
        )
        self._record(result)
        return result

    def start_session(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        result = self.service.start_session(
            session_id
        )
        self._record(result)
        return result

    def close_session(
        self,
        session_id: str,
    ) -> ProjectSessionContract:
        result = self.service.close_session(
            session_id
        )
        self._record(result)
        return result

    def remove_session(
        self,
        session_id: str,
    ) -> bool:
        result = self.service.remove_session(
            session_id
        )
        self.request_count += 1
        return result

    def project_sessions(
        self,
        project_id: str,
    ) -> tuple[ProjectSessionContract, ...]:
        result = self.service.project_sessions(
            project_id
        )
        self.request_count += 1
        return result

    def active_sessions(
        self,
    ) -> tuple[ProjectSessionContract, ...]:
        result = self.service.active_sessions()
        self.request_count += 1
        return result

    def execute(
        self,
        request: dict[str, object],
    ) -> object:
        if not isinstance(
            request,
            dict,
        ):
            raise TypeError(
                "adapter request must dict"
            )

        if not request:
            raise ValueError(
                "adapter request required"
            )

        result = self.service.execute(
            request
        )
        self.request_count += 1
        return result

    def ready(self) -> bool:
        return (
            isinstance(
                self.service,
                ProjectSessionServiceContract,
            )
            and self.service.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "ready": self.ready(),
            "request_count": self.request_count,
            "service": type(
                self.service
            ).__name__,
            "service_ready": self.service.ready(),
        }

    def _record(
        self,
        result: Any,
    ) -> None:
        if not isinstance(
            result,
            ProjectSessionContract,
        ):
            raise TypeError(
                "project session service returned "
                "invalid ProjectSessionContract"
            )

        self.request_count += 1


__all__ = [
    "ProjectSessionApplicationAdapter",
]
