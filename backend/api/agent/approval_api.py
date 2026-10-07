"""审批 API：单条 + 批量（Claude Code 式）。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

from backend.application.agent_loop.pending_gate import get_gate

router = APIRouter(prefix="/api/agent", tags=["agent-approval"])


def _ok(data: Any) -> JSONResponse:
    return JSONResponse(status_code=200, content={"ok": True, "data": data})


def _err(code: int, msg: str) -> JSONResponse:
    return JSONResponse(
        status_code=code,
        content={"ok": False, "error": {"code": "ERR", "message": msg}},
    )


@router.post("/approve/{edit_id}")
async def approve_one(edit_id: str) -> JSONResponse:
    ok = await get_gate().approve(edit_id)
    return _ok({"edit_id": edit_id, "approved": ok})


@router.post("/reject/{edit_id}")
async def reject_one(edit_id: str) -> JSONResponse:
    ok = await get_gate().reject(edit_id)
    return _ok({"edit_id": edit_id, "rejected": ok})


@router.post("/approve-batch")
async def approve_batch(payload: dict = Body(...)) -> JSONResponse:
    """批量批准：body={edit_ids: [str, ...]}"""
    ids = list(payload.get("edit_ids") or [])
    if not ids:
        return _err(400, "edit_ids required")
    gate = get_gate()
    results = {}
    for eid in ids:
        results[eid] = await gate.approve(str(eid))
    return _ok({
        "requested": len(ids),
        "approved": sum(1 for v in results.values() if v),
        "results": results,
    })


@router.post("/reject-batch")
async def reject_batch(payload: dict = Body(...)) -> JSONResponse:
    ids = list(payload.get("edit_ids") or [])
    if not ids:
        return _err(400, "edit_ids required")
    gate = get_gate()
    results = {}
    for eid in ids:
        results[eid] = await gate.reject(str(eid))
    return _ok({
        "requested": len(ids),
        "rejected": sum(1 for v in results.values() if v),
        "results": results,
    })


@router.get("/pending")
async def list_pending() -> JSONResponse:
    """列出所有挂起编辑（跨重启）。"""
    gate = get_gate()
    return _ok({"pending": gate.list_pending()})


__all__ = ["router"]
