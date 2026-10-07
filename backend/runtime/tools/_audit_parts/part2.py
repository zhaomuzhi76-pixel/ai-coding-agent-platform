"""Part 2 of audit.py."""
from __future__ import annotations
from backend.core.observability.silent import swallow

from .part1 import (ToolArgumentValue, ZoneInfo, _DB_PATH, datetime, json, sqlite3,)  # noqa
from .part1 import ToolAuditRecord  # noqa
from .part1 import _ensure_schema  # noqa

class ToolAudit:
    """In-memory tool execution audit boundary."""

    VERSION = "3.0"
    TIMEZONE = ZoneInfo("Asia/Shanghai")

    def __init__(self, *, persist: bool = True) -> None:
        self._records: list[ToolAuditRecord] = []
        self._persist = persist
        if persist:
            try:
                _ensure_schema()
            except Exception:
                self._persist = False

    def record(
        self,
        *,
        trace_id: str,
        tool: str,
        success: bool,
        duration: float = 0.0,
        error: str | None = None,
        session_id: str | None = None,
        agent_id: str | None = None,
        action: str | None = None,
        resource: str | None = None,
        approval_id: str | None = None,
        risk_level: str = "safe",
        metadata: dict[str, ToolArgumentValue] | None = None,
        tenant_id: str = "",
    ) -> None:
        if not trace_id.strip():
            raise ValueError("trace_id required")

        if not tool.strip():
            raise ValueError("tool required")

        if duration < 0:
            raise ValueError("duration cannot be negative")

        ts = datetime.now(self.TIMEZONE).isoformat()
        rec = ToolAuditRecord(
            trace_id=trace_id, tool=tool, success=success,
            duration=duration, error=error,
            session_id=session_id, agent_id=agent_id,
            action=action, resource=resource,
            approval_id=approval_id, risk_level=risk_level,
            metadata=dict(metadata or {}), timestamp=ts,
        )
        self._records.append(rec)

        if self._persist:
            try:
                with sqlite3.connect(_DB_PATH) as conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO tool_audit("
                        "trace_id, tenant_id, session_id, agent_id, tool, "
                        "action, resource, approval_id, risk_level, success, "
                        "duration, error, metadata_json, timestamp) "
                        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            trace_id, tenant_id or "",
                            session_id or "", agent_id or "",
                            tool, action or "", resource or "",
                            approval_id or "", risk_level,
                            1 if success else 0, float(duration),
                            error or "",
                            json.dumps(rec.metadata, ensure_ascii=False, default=str),
                            ts,
                        ),
                    )
            except Exception as e:
                swallow("runtime.tools._audit_parts.part2:82", e, level="warn")

    def history(
        self,
    ) -> list[ToolAuditRecord]:
        return list(self._records)

    def history_db(
        self,
        *,
        tenant_id: str = "",
        limit: int = 100,
    ) -> list[dict]:
        """从 metrics.db 拉历史（跨重启）。tenant_id='' 表示全部。"""
        try:
            with sqlite3.connect(_DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                if tenant_id:
                    rows = conn.execute(
                        "SELECT * FROM tool_audit WHERE tenant_id=? "
                        "ORDER BY timestamp DESC LIMIT ?",
                        (tenant_id, int(limit)),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT * FROM tool_audit "
                        "ORDER BY timestamp DESC LIMIT ?",
                        (int(limit),),
                    ).fetchall()
                return [dict(r) for r in rows]
        except Exception:
            return []

    def count_db(self, tenant_id: str = "") -> int:
        try:
            with sqlite3.connect(_DB_PATH) as conn:
                if tenant_id:
                    return int(conn.execute(
                        "SELECT COUNT(*) FROM tool_audit WHERE tenant_id=?",
                        (tenant_id,)).fetchone()[0])
                return int(conn.execute(
                    "SELECT COUNT(*) FROM tool_audit").fetchone()[0])
        except Exception:
            return 0

    def latest(
        self,
        limit: int = 10,
    ) -> list[ToolAuditRecord]:
        if limit < 0:
            raise ValueError("limit cannot be negative")

        if limit == 0:
            return []

        return self._records[-limit:]

    def count(self) -> int:
        return len(self._records)

    def success_count(self) -> int:
        return sum(
            record.success
            for record in self._records
        )

    def failure_count(self) -> int:
        return sum(
            not record.success
            for record in self._records
        )

    def tool_count(
        self,
        tool_name: str,
    ) -> int:
        if not tool_name.strip():
            raise ValueError("tool name required")

        return sum(
            record.tool == tool_name
            for record in self._records
        )

    def clear(self) -> None:
        self._records.clear()

    def ready(self) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, ToolArgumentValue]:
        return {
            "persist": getattr(self, "_persist", False),
            "db_path": str(_DB_PATH),
            "name": "ToolAudit",
            "version": self.VERSION,
            "ready": self.ready(),
            "count": self.count(),
            "success": self.success_count(),
            "failure": self.failure_count(),
        }

__all__ = [
    "ToolAudit",
    "ToolAuditRecord",
]
