from __future__ import annotations

from backend.api.project_session.project_session_agent_request_factory import (
    ProjectSessionAgentRequestFactory,
)
from backend.api.project_session.project_session_api_contract import (
    ProjectSessionAPIContract,
)
from backend.api.project_session.project_session_api_diagnostics import (
    ProjectSessionAPIDiagnosticsMixin,
)
from backend.api.project_session.project_session_api_runtime_submission import (
    ProjectSessionAPIRuntimeSubmissionMixin,
)
from backend.api.project_session.project_session_api_support import (
    ProjectSessionAPISupport,
)
from backend.application.project_session.project_session_adapter_contract import (
    ProjectSessionApplicationAdapterContract,
)
from backend.application.runtime_submission_contract import (
    ApplicationRuntimeSubmissionProtocol,
)


class ProjectSessionAPI(
    ProjectSessionAPIRuntimeSubmissionMixin,
    ProjectSessionAPIDiagnosticsMixin,
    ProjectSessionAPIContract,
):
    """Project-session HTTP application facade."""

    VERSION = "3.1"

    def __init__(
        self,
        adapter: ProjectSessionApplicationAdapterContract,
        runtime_submission: ApplicationRuntimeSubmissionProtocol,
        support: ProjectSessionAPISupport | None = None,
        request_factory: ProjectSessionAgentRequestFactory | None = None,
    ) -> None:
        self._validate_adapter(adapter)

        self.adapter = adapter
        self.support = (
            support
            or ProjectSessionAPISupport()
        )

        self._init_runtime_submission(
            runtime_submission,
            self.support,
            request_factory,
        )

        self.request_count = 0

    def create(
        self,
        payload: dict[str, object],
    ) -> dict[str, object]:
        data = self.support.payload(payload)

        result = self.adapter.create_session(
            project_id=self.support.required(
                data.get("project_id"),
                "project_id",
            ),
            session_id=self.support.optional(
                data.get("session_id")
            ),
            workspace_id=self.support.optional(
                data.get("workspace_id")
            ),
            runtime_id=self.support.optional(
                data.get("runtime_id")
            ),
            metadata=self.support.metadata(
                data.get("metadata")
            ),
        )
        return self._session(result)

    def get(
        self,
        session_id: str,
    ) -> dict[str, object]:
        return self._session(
            self.adapter.get_session(
                self.support.session_id(session_id)
            )
        )

    def start(
        self,
        session_id: str,
    ) -> dict[str, object]:
        return self._session(
            self.adapter.start_session(
                self.support.session_id(session_id)
            )
        )

    def close(
        self,
        session_id: str,
    ) -> dict[str, object]:
        return self._session(
            self.adapter.close_session(
                self.support.session_id(session_id)
            )
        )

    def remove(
        self,
        session_id: str,
    ) -> dict[str, object]:
        normalized = self.support.session_id(
            session_id
        )
        removed = self.adapter.remove_session(
            normalized
        )
        self.request_count += 1
        return {
            "session_id": normalized,
            "removed": bool(removed),
        }

    def project_sessions(
        self,
        project_id: str,
    ) -> dict[str, object]:
        normalized = self.support.required(
            project_id,
            "project_id",
        )
        values = self.adapter.project_sessions(
            normalized
        )
        self.request_count += 1
        return {
            "project_id": normalized,
            "sessions": self.support.result.sessions(
                values
            ),
            "count": len(values),
        }

    def active_sessions(
        self,
    ) -> dict[str, object]:
        values = self.adapter.active_sessions()
        self.request_count += 1
        return {
            "sessions": self.support.result.sessions(
                values
            ),
            "count": len(values),
        }

    def ready(self) -> bool:
        return (
            self.adapter.ready()
            and self.support.ready()
            and self.runtime_submission_ready()
        )

    def dump(self) -> dict[str, object]:
        result = {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "request_count": self.request_count,
        }
        result.update(
            self.runtime_submission_dump()
        )
        return result

    def _session(
        self,
        value: object,
    ) -> dict[str, object]:
        self.request_count += 1
        return self.support.result.session(value)

    @staticmethod
    def _validate_adapter(
        adapter: object,
    ) -> None:
        if not isinstance(
            adapter,
            ProjectSessionApplicationAdapterContract,
        ):
            raise TypeError(
                "adapter must "
                "ProjectSessionApplicationAdapterContract"
            )

        if not adapter.ready():
            raise RuntimeError(
                "project session application adapter "
                "not ready"
            )


__all__ = [
    "ProjectSessionAPI",
]
