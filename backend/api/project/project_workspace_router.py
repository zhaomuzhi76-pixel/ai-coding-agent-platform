from __future__ import annotations

from fastapi import APIRouter

from backend.api.project.project_registration_api import (
    ProjectRegistrationAPI,
)
from backend.api.project.project_workspace_router_support import (
    ProjectWorkspaceRouterSupport,
)


class ProjectWorkspaceRouter:
    """
    Workspace HTTP route registration.

    Owns:
        - route declaration
        - handler binding

    Does not own:
        - project registry
        - filesystem
        - workspace persistence
        - agent runtime
    """

    VERSION = "1.0"
    PREFIX = "/api/projects"

    def __init__(
        self,
        api: ProjectRegistrationAPI,
    ) -> None:
        self.support = (
            ProjectWorkspaceRouterSupport(api)
        )
        self.router = APIRouter()
        self._register()

    def _register(self) -> None:
        self.router.get(
            f"{self.PREFIX}/{{project_id}}/workspace/tree"
        )(self.tree)

        self.router.get(
            f"{self.PREFIX}/{{project_id}}/workspace/file"
        )(self.file)

        self.router.put(
            f"{self.PREFIX}/{{project_id}}/workspace/file"
        )(self.write)

    async def tree(
        self,
        project_id: str,
        path: str = "",
    ):
        return await self.support.tree(
            project_id,
            path,
        )

    async def file(
        self,
        project_id: str,
        path: str,
    ):
        return await self.support.file(
            project_id,
            path,
        )

    async def write(
        self,
        project_id: str,
        payload: dict[str, object],
    ):
        return await self.support.write(
            project_id,
            payload,
        )

    def ready(self) -> bool:
        return bool(
            self.router.routes
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "prefix": self.PREFIX,
            "route_count": len(
                self.router.routes,
            ),
            "ready": self.ready(),
        }


__all__ = [
    "ProjectWorkspaceRouter",
]
