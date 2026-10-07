from __future__ import annotations

from backend.api.project_session.binding.project_session_api_binding import (
    ProjectSessionAPIBinding,
)
from backend.api.project_session.project_session_api_factory import (
    ProjectSessionAPIFactory,
)
from backend.application.project_session.project_session_adapter_contract import (
    ProjectSessionApplicationAdapterContract,
)
from backend.application.runtime_submission_contract import (
    ApplicationRuntimeSubmissionProtocol,
)


class ProjectSessionAPIBindingFactory:
    """
    API project-session binding construction boundary.

    Receives only already assembled application contracts.
    """

    VERSION = "2.0"

    def create(
        self,
        adapter: ProjectSessionApplicationAdapterContract,
        runtime_submission: ApplicationRuntimeSubmissionProtocol,
        api_factory: ProjectSessionAPIFactory | None = None,
    ) -> ProjectSessionAPIBinding:
        if not self.ready():
            raise RuntimeError(
                "project session API binding factory unavailable"
            )

        if not isinstance(
            adapter,
            ProjectSessionApplicationAdapterContract,
        ):
            raise TypeError(
                "adapter contract required"
            )

        if not isinstance(
            runtime_submission,
            ApplicationRuntimeSubmissionProtocol,
        ):
            raise TypeError(
                "runtime submission contract required"
            )

        factory = (
            api_factory
            or ProjectSessionAPIFactory()
        )

        if not factory.ready():
            raise RuntimeError(
                "project session API factory unavailable"
            )

        binding = ProjectSessionAPIBinding(
            adapter=adapter,
            runtime_submission=runtime_submission,
            api_factory=factory,
        )

        if not binding.ready():
            raise RuntimeError(
                "project session API binding unavailable"
            )

        return binding

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ProjectSessionAPIBindingFactory",
]
