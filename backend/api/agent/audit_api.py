"""审计与待审批历史 HTTP 端点（L1+L2 持久化的对外接口）。

工业级契约：
    - GET /api/agent/audit?tenant_id=&limit=     工具审计历史
    - GET /api/agent/pending-history?tenant_id=&limit=
                                                  待审批编辑历史（跨重启）
    - 直接查 ~/.biancheng/metrics.db（不依赖内存单例）

X-Tenant-Id 请求头（可选）自动注入 tenant_id（未提供则全租户）。
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/agent", tags=["agent"])

_DB_DIR = Path.home() / ".biancheng"
_DB_PATH = _DB_DIR / "metrics.db"


def _query(sql: str, params: tuple) -> list[dict]:
    try:
        with sqlite3.connect(_DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(r) for r in conn.execute(sql, params).fetchall()]
    except Exception:
        return []


@router.get("/audit")
async def list_audit(
    tenant_id: str = "",
    limit: int = 100,
    x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
) -> JSONResponse:
    """工具审计历史。tenant_id 优先用 header，其次 query。"""
    tid = (x_tenant_id or tenant_id or "").strip()
    limit = max(1, min(int(limit), 1000))
    if tid:
        rows = _query(
            "SELECT trace_id, tenant_id, session_id, agent_id, tool, action, "
            "resource, approval_id, risk_level, success, duration, error, "
            "metadata_json, timestamp FROM tool_audit WHERE tenant_id=? "
            "ORDER BY timestamp DESC LIMIT ?",
            (tid, limit))
    else:
        rows = _query(
            "SELECT trace_id, tenant_id, session_id, agent_id, tool, action, "
            "resource, approval_id, risk_level, success, duration, error, "
            "metadata_json, timestamp FROM tool_audit "
            "ORDER BY timestamp DESC LIMIT ?",
            (limit,))
    return JSONResponse(status_code=200, content={
        "ok": True, "tenant_id": tid, "count": len(rows), "items": rows,
    })


@router.get("/pending-history")
async def list_pending_history(
    tenant_id: str = "",
    limit: int = 100,
    x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
) -> JSONResponse:
    """待审批编辑历史（跨重启，含决策 + 清理时间）。"""
    tid = (x_tenant_id or tenant_id or "").strip()
    limit = max(1, min(int(limit), 1000))
    if tid:
        rows = _query(
            "SELECT edit_id, tenant_id, action, path, diff, status, decision, "
            "created_at, decided_at, cleaned_at FROM pending_edits "
            "WHERE tenant_id=? ORDER BY created_at DESC LIMIT ?",
            (tid, limit))
    else:
        rows = _query(
            "SELECT edit_id, tenant_id, action, path, diff, status, decision, "
            "created_at, decided_at, cleaned_at FROM pending_edits "
            "ORDER BY created_at DESC LIMIT ?",
            (limit,))
    return JSONResponse(status_code=200, content={
        "ok": True, "tenant_id": tid, "count": len(rows), "items": rows,
    })


__all__ = ["router"]
