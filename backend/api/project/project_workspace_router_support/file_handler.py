"""Handle file read request."""
from __future__ import annotations

from fastapi.responses import JSONResponse

from backend.api.project.project_workspace_router_support.binder import (
    resolve_workspace,
)
from backend.api.project.project_workspace_router_support.error_response import (
    error_response,
)
from backend.api.project.project_workspace_router_support.errors import (
    WorkspaceResourceError,
)


async def handle_file(api, project_id: str, path: str) -> JSONResponse:
    try:
        service = await resolve_workspace(api, project_id)
        content = service.get_service().read_file(path)
        return JSONResponse(
            status_code=200,
            content={
                "project_id": project_id,
                "path": path,
                "content": content,
            },
        )
    except KeyError as error:
        return error_response(404, str(error))
    except (ValueError, WorkspaceResourceError) as error:
        return error_response(400, str(error))
    except Exception as error:
        return error_response(500, str(error))
