from __future__ import annotations

from backend.application.operational.project_session.project_session_operational_contract import (
    ProjectSessionOperationalContract,
)
from backend.application.operational.project_session.startup.project_session_startup_binding import (
    ProjectSessionStartupBinding,
)


class ProjectSessionStartupBindingFactory:
    """
    Construction boundary for startup project-session binding.
    """

    VERSION = "1.0"

    def create(
        self,
        operational: ProjectSessionOperationalContract,
    ) -> ProjectSessionStartupBinding:
        if not self.ready():
            raise RuntimeError(
                "project session startup binding factory unavailable"
            )

        if not isinstance(
            operational,
            ProjectSessionOperationalContract,
        ):
            raise TypeError(
                "project session operational contract required"
            )

        binding = ProjectSessionStartupBinding(
            operational=operational,
        )

        if not binding.ready():
            raise RuntimeError(
                "project session startup binding unavailable"
            )

        return binding

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ProjectSessionStartupBindingFactory",
]
