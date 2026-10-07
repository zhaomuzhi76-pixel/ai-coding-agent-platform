"""Handle file write request."""
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


async def handle_write(
    api, project_id: str, payload: dict,
) -> JSONResponse:
    try:
        path = payload.get("path")
        content = payload.get("content")
        if not isinstance(path, str):
            raise WorkspaceResourceError("file path required")
        if not isinstance(content, str):
            raise WorkspaceResourceError("file content required")
        binding = await resolve_workspace(api, project_id)
        ops = binding.get_operations()
        result = ops.write_file(path, content)
        if hasattr(result, "__await__"):
            await result
        return JSONResponse(
            status_code=200,
            content={
                "project_id": project_id,
                "path": path,
                "written": True,
            },
        )
    except KeyError as error:
        return error_response(404, str(error))
    except (ValueError, WorkspaceResourceError) as error:
        return error_response(400, str(error))
    except Exception as error:
        return error_response(500, str(error))
