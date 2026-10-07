"""PendingGate: 全局挂起编辑器 + SQLite 落库（跨重启可恢复）。

工业级契约：
    - request(): 创建 pending，注册等待事件，落库
    - wait(): 异步等待批准/拒绝/超时（不阻塞事件循环）
    - approve() / reject(): 前端 WS 调用，落库
    - cleanup(): 标记 cleaned（不删，留审计）
    - history_db(): 从库拉历史（跨重启）
    - 单例（全局唯一队列）
    - 与 ApprovalGate（proposal 用）隔离，不重复职责
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import asyncio
import sqlite3
import time
from pathlib import Path
from typing import Optional

from .pending_edit import PendingEdit

_DEFAULT_TIMEOUT_SEC = 300.0

_DB_DIR = Path.home() / ".biancheng"
_DB_PATH = _DB_DIR / "metrics.db"


def _ensure_schema() -> None:
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(_DB_PATH) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS pending_edits (
                edit_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL DEFAULT '',
                action TEXT NOT NULL,
                path TEXT NOT NULL,
                old_content TEXT,
                new_content TEXT,
                diff TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'pending',
                decision TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL,
                decided_at REAL NOT NULL DEFAULT 0,
                cleaned_at REAL NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_pending_status
                ON pending_edits(status, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_pending_tenant
                ON pending_edits(tenant_id, status, created_at DESC);
        """)


class PendingGate:
    VERSION = "1.1"

    def __init__(self, *, persist: bool = True) -> None:
        self._pending: dict[str, PendingEdit] = {}
        self._events: dict[str, asyncio.Event] = {}
        self._decisions: dict[str, str] = {}
        self._lock = asyncio.Lock()
        self._persist = persist
        if persist:
            try:
                _ensure_schema()
            except Exception:
                self._persist = False

    def _db_insert(self, edit: PendingEdit, tenant_id: str = "") -> None:
        if not self._persist:
            return
        try:
            with sqlite3.connect(_DB_PATH) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO pending_edits("
                    "edit_id, tenant_id, action, path, old_content, "
                    "new_content, diff, status, decision, created_at) "
                    "VALUES(?,?,?,?,?,?,?,'pending','',?)",
                    (edit.edit_id, tenant_id or "", edit.action, edit.path,
                     edit.old_content, edit.new_content, edit.diff,
                     float(edit.created_at)),
                )
        except Exception as e:
            swallow("application.agent_loop.pending_gate:84", e)

    def _db_decide(self, edit_id: str, decision: str) -> None:
        if not self._persist:
            return
        try:
            with sqlite3.connect(_DB_PATH) as conn:
                conn.execute(
                    "UPDATE pending_edits SET decision=?, "
                    "status=?, decided_at=? WHERE edit_id=?",
                    (decision, decision, time.time(), edit_id),
                )
        except Exception as e:
            swallow("application.agent_loop.pending_gate:97", e)

    def _db_cleanup(self, edit_id: str) -> None:
        if not self._persist:
            return
        try:
            with sqlite3.connect(_DB_PATH) as conn:
                conn.execute(
                    "UPDATE pending_edits SET status='cleaned', "
                    "cleaned_at=? WHERE edit_id=?",
                    (time.time(), edit_id),
                )
        except Exception as e:
            swallow("application.agent_loop.pending_gate:110", e)

    async def request(self, edit: PendingEdit, *, tenant_id: str = "") -> str:
        async with self._lock:
            self._pending[edit.edit_id] = edit
            self._events[edit.edit_id] = asyncio.Event()
            self._decisions.pop(edit.edit_id, None)
        self._db_insert(edit, tenant_id)
        return edit.edit_id

    async def wait(
        self, edit_id: str,
        timeout: float = _DEFAULT_TIMEOUT_SEC,
    ) -> str:
        ev = self._events.get(edit_id)
        if ev is None:
            return "unknown"
        try:
            await asyncio.wait_for(ev.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            async with self._lock:
                self._decisions[edit_id] = "timeout"
            self._db_decide(edit_id, "timeout")
            return "timeout"
        return self._decisions.get(edit_id, "unknown")

    async def approve(self, edit_id: str) -> bool:
        async with self._lock:
            ev = self._events.get(edit_id)
            if ev is None:
                return False
            self._decisions[edit_id] = "approved"
            ev.set()
        self._db_decide(edit_id, "approved")
        return True

    async def reject(self, edit_id: str) -> bool:
        async with self._lock:
            ev = self._events.get(edit_id)
            if ev is None:
                return False
            self._decisions[edit_id] = "rejected"
            ev.set()
        self._db_decide(edit_id, "rejected")
        return True

    def get(self, edit_id: str) -> Optional[PendingEdit]:
        return self._pending.get(edit_id)

    def list_pending(self) -> list[dict]:
        return [e.to_wire() for e in self._pending.values()]

    def cleanup(self, edit_id: str) -> None:
        self._pending.pop(edit_id, None)
        self._events.pop(edit_id, None)
        self._decisions.pop(edit_id, None)
        self._db_cleanup(edit_id)

    def history_db(
        self, *, tenant_id: str = "", limit: int = 100,
    ) -> list[dict]:
        """从库拉历史（跨重启）。tenant_id='' 表示全部。"""
        if not self._persist:
            return []
        try:
            with sqlite3.connect(_DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                if tenant_id:
                    rows = conn.execute(
                        "SELECT * FROM pending_edits WHERE tenant_id=? "
                        "ORDER BY created_at DESC LIMIT ?",
                        (tenant_id, int(limit)),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT * FROM pending_edits "
                        "ORDER BY created_at DESC LIMIT ?",
                        (int(limit),),
                    ).fetchall()
                return [dict(r) for r in rows]
        except Exception:
            return []

    def dump(self) -> dict:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "pending": len(self._pending),
            "persist": getattr(self, "_persist", False),
        }


_GATE: Optional[PendingGate] = None


def get_gate() -> PendingGate:
    global _GATE
    if _GATE is None:
        _GATE = PendingGate()
    return _GATE


__all__ = ["PendingGate", "get_gate"]
