"""Project workspace router support facade."""
from __future__ import annotations

from backend.api.project.project_registration_api import (
    ProjectRegistrationAPI,
)
from backend.api.project.project_workspace_router_support.binder import (
    resolve_workspace,
)
from backend.api.project.project_workspace_router_support.error_response import (
    error_response,
)
from backend.api.project.project_workspace_router_support.file_handler import (
    handle_file,
)
from backend.api.project.project_workspace_router_support.tree_handler import (
    handle_tree,
)
from backend.api.project.project_workspace_router_support.write_handler import (
    handle_write,
)


class ProjectWorkspaceRouterSupport:
    VERSION = "1.0"

    def __init__(self, api: ProjectRegistrationAPI) -> None:
        if not isinstance(api, ProjectRegistrationAPI):
            raise TypeError("api must ProjectRegistrationAPI")
        if not api.ready():
            raise RuntimeError("project registration api not ready")
        self.api = api

    async def workspace(self, project_id: str):
        return await resolve_workspace(self.api, project_id)

    async def tree(self, project_id: str, path: str = ""):
        return await handle_tree(self.api, project_id, path)

    async def file(self, project_id: str, path: str):
        return await handle_file(self.api, project_id, path)

    async def write(self, project_id: str, payload: dict):
        return await handle_write(self.api, project_id, payload)

    @staticmethod
    def error(status_code: int, message: str):
        return error_response(status_code, message)


__all__ = ["ProjectWorkspaceRouterSupport"]
