from __future__ import annotations

from backend.workspace.project.session.service.project_session_service_operations import (
    ProjectSessionServiceOperations,
)
from backend.workspace.project.session.service.project_session_service_support import (
    ProjectSessionServiceSupport,
)


class ProjectSessionServiceDispatcher:
    """
    Service operation dispatch boundary.

    Owns:
        - operation routing
        - request-shape validation

    Does not own:
        - business state
        - session lifecycle
        - registry storage
    """

    VERSION = "1.0"

    def __init__(
        self,
        operations: ProjectSessionServiceOperations,
        support: ProjectSessionServiceSupport,
    ) -> None:
        self.operations = operations
        self.support = support

    def execute(
        self,
        request: dict[str, object],
    ) -> object:
        if not isinstance(request, dict):
            raise TypeError("service request must dict")

        operation = self.support.operation(
            request.get("operation")
        )

        handlers = {
            "create": self.operations.create_session,
            "get": self.operations.get_session,
            "start": self.operations.start_session,
            "close": self.operations.close_session,
            "remove": self.operations.remove_session,
            "project_sessions": (
                self.operations.project_sessions
            ),
            "active_sessions": (
                self.operations.active_sessions
            ),
        }

        handler = handlers.get(operation)
        if handler is None:
            raise ValueError(
                f"unsupported session operation: {operation}"
            )

        arguments = dict(request)
        arguments.pop("operation", None)
        return handler(**arguments)

    def ready(self) -> bool:
        return (
            self.operations.ready()
            and self.support.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ProjectSessionServiceDispatcher",
]
