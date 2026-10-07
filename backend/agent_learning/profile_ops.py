"""L2 桥接：UserProfileStore + scope 过滤。"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any

from backend.agent_learning.kinds import (
    AUTO_APPLY_THRESHOLD, VISIBLE_THRESHOLD,
)
from backend.agent_learning.scope import RuleScope, is_active_for

_DB = Path.home() / ".biancheng" / "global" / "global.db"


def _ensure_db() -> None:
    from backend.code_intelligence.memory.user_profile.schema import init_schema
    _DB.parent.mkdir(parents=True, exist_ok=True)
    init_schema(_DB)


def list_all(
    min_confidence: int = VISIBLE_THRESHOLD,
    *, scope: str = "", workspace: str = "",
) -> list[dict[str, Any]]:
    _ensure_db()
    sql = ("SELECT id, category, key, value, confidence, sample_count, "
           "last_used_at, created_at, scope, workspace "
           "FROM preferences WHERE confidence >= ?")
    args: list[Any] = [min_confidence]
    if scope:
        sql += " AND scope = ?"; args.append(scope)
    if workspace:
        sql += " AND (workspace = ? OR workspace = '')"
        args.append(workspace)
    sql += " ORDER BY confidence DESC, last_used_at DESC"
    with sqlite3.connect(_DB) as conn:
        rows = conn.execute(sql, args).fetchall()
    return [
        {"id": r[0], "kind": r[1], "key": r[2], "value": r[3],
         "confidence": r[4], "sample_count": r[5],
         "last_used_at": r[6], "created_at": r[7],
         "scope": r[8] or "global", "workspace": r[9] or "",
         "auto_applied": r[4] >= AUTO_APPLY_THRESHOLD}
        for r in rows
    ]


def upsert(
    kind: str, key: str, value: str, confidence: int = 60,
    *, scope: str = RuleScope.GLOBAL.value, workspace: str = "",
) -> dict[str, Any]:
    _ensure_db()
    now = time.time()
    with sqlite3.connect(_DB) as conn:
        cur = conn.execute(
            "SELECT id, confidence FROM preferences "
            "WHERE category=? AND key=? AND value=?",
            (kind, key, value)).fetchone()
        if cur:
            new_conf = min(100, cur[1] + 5)
            conn.execute(
                "UPDATE preferences SET confidence=?, "
                "sample_count=sample_count+1, last_used_at=?, "
                "scope=?, workspace=? WHERE id=?",
                (new_conf, now, scope, workspace, cur[0]))
            return {"id": cur[0], "confidence": new_conf, "updated": True}
        cur = conn.execute(
            "INSERT INTO preferences(category, key, value, confidence, "
            "sample_count, last_used_at, created_at, scope, workspace) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (kind, key, value, confidence, 1, now, now, scope, workspace))
    return {"id": cur.lastrowid, "confidence": confidence,
            "created": True, "scope": scope}


def delete(pref_id: int) -> bool:
    _ensure_db()
    with sqlite3.connect(_DB) as conn:
        cur = conn.execute("DELETE FROM preferences WHERE id=?", (pref_id,))
    return cur.rowcount > 0


def update_confidence(pref_id: int, confidence: int) -> bool:
    _ensure_db()
    c = max(0, min(100, int(confidence)))
    with sqlite3.connect(_DB) as conn:
        cur = conn.execute(
            "UPDATE preferences SET confidence=? WHERE id=?", (c, pref_id))
    return cur.rowcount > 0


def update_scope(pref_id: int, scope: str, workspace: str = "") -> bool:
    _ensure_db()
    with sqlite3.connect(_DB) as conn:
        cur = conn.execute(
            "UPDATE preferences SET scope=?, workspace=? WHERE id=?",
            (scope, workspace, pref_id))
    return cur.rowcount > 0


def render_context(
    auto_only: bool = True, limit: int = 12, *, workspace: str = "",
) -> str:
    min_conf = AUTO_APPLY_THRESHOLD if auto_only else VISIBLE_THRESHOLD
    active = [
        p for p in list_all(min_confidence=min_conf, workspace=workspace)
        if is_active_for(p.get("scope", "global"),
                         p.get("workspace", ""), workspace)
    ][:limit]
    if not active:
        return ""
    lines = ["[User preferences learned from past sessions]"]
    by_kind: dict[str, list[dict]] = {}
    for p in active:
        by_kind.setdefault(p["kind"], []).append(p)
    for kind in sorted(by_kind):
        for p in by_kind[kind]:
            lines.append(
                f"- [{kind}][{p.get('scope','global')}] "
                f"{p['key']}: {p['value']} (conf {p['confidence']})")
    return "\n".join(lines)


__all__ = ["list_all", "upsert", "delete", "update_confidence",
           "update_scope", "render_context"]
