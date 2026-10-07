"""Handle tree listing request.

L3 装配：走 FileTreeService（filter + index + pagination）。
契约不变：{project_id, path, entries, count} + total/more/next_cursor。
"""
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
from backend.workspace.tree.service import FileTreeService
from backend.workspace.tree.pagination.cursor import PaginationSpec


async def handle_tree(api, project_id: str, path: str = "") -> JSONResponse:
    try:
        service = await resolve_workspace(api, project_id)
        fs = service.get_filesystem()

        tree = FileTreeService(fs)
        page = tree.list_dir(path, PaginationSpec(limit=500))

        return JSONResponse(
            status_code=200,
            content={
                "project_id": project_id,
                "path": path,
                "entries": list(page.entries),
                "count": len(page.entries),
                "total": page.total,
                "more": page.more,
                "next_cursor": page.next_cursor,
            },
        )
    except KeyError as error:
        return error_response(404, str(error))
    except (ValueError, WorkspaceResourceError) as error:
        return error_response(400, str(error))
    except Exception as error:
        import traceback
        traceback.print_exc()
        return error_response(500, str(error))
