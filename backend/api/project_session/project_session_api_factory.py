from __future__ import annotations

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


class ProjectSessionAPIFactory:
    """
    Project-session API construction boundary.
    """

    VERSION = "2.1"

    def create_api(
        self,
        adapter: ProjectSessionApplicationAdapterContract,
        runtime_submission: ApplicationRuntimeSubmissionProtocol,
    ) -> ProjectSessionAPI:
        if not self.ready():
            raise RuntimeError(
                "project session API factory unavailable"
            )

        self._validate_adapter(adapter)
        self._validate_runtime_submission(
            runtime_submission
        )

        api = ProjectSessionAPI(
            adapter=adapter,
            runtime_submission=runtime_submission,
        )

        if not api.ready():
            raise RuntimeError(
                "project session API unavailable"
            )

        return api

    def create_router(
        self,
        adapter: ProjectSessionApplicationAdapterContract,
        runtime_submission: ApplicationRuntimeSubmissionProtocol,
    ) -> ProjectSessionAPIRouter:
        api = self.create_api(
            adapter=adapter,
            runtime_submission=runtime_submission,
        )

        router = ProjectSessionAPIRouter(api)

        if not router.ready():
            raise RuntimeError(
                "project session API router unavailable"
            )

        return router

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }

    @staticmethod
    def _validate_adapter(adapter: object) -> None:
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

    @staticmethod
    def _validate_runtime_submission(
        runtime_submission: object,
    ) -> None:
        if not isinstance(
            runtime_submission,
            ApplicationRuntimeSubmissionProtocol,
        ):
            raise TypeError(
                "runtime_submission must implement "
                "ApplicationRuntimeSubmissionProtocol"
            )

        if not runtime_submission.ready():
            raise RuntimeError(
                "runtime submission not ready"
            )


__all__ = [
    "ProjectSessionAPIFactory",
]
