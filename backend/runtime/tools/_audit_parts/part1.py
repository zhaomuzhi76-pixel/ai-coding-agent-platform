"""Part 1 of audit.py."""
from __future__ import annotations

import json

import sqlite3

from dataclasses import dataclass, field

from datetime import datetime

from pathlib import Path

from zoneinfo import ZoneInfo

from backend.core.tools.argument_contract import ToolArgumentValue

_DB_DIR = Path.home() / ".biancheng"

_DB_PATH = _DB_DIR / "metrics.db"

def _ensure_schema() -> None:
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(_DB_PATH) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS tool_audit (
                trace_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL DEFAULT '',
                session_id TEXT NOT NULL DEFAULT '',
                agent_id TEXT NOT NULL DEFAULT '',
                tool TEXT NOT NULL,
                action TEXT NOT NULL DEFAULT '',
                resource TEXT NOT NULL DEFAULT '',
                approval_id TEXT NOT NULL DEFAULT '',
                risk_level TEXT NOT NULL DEFAULT 'safe',
                success INTEGER NOT NULL,
                duration REAL NOT NULL DEFAULT 0,
                error TEXT NOT NULL DEFAULT '',
                metadata_json TEXT NOT NULL DEFAULT '{}',
                timestamp TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_tool_audit_tenant
                ON tool_audit(tenant_id, timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_tool_audit_tool
                ON tool_audit(tool, timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_tool_audit_trace
                ON tool_audit(trace_id);
        """)

@dataclass(frozen=True, slots=True)
class ToolAuditRecord:
    trace_id: str
    tool: str
    success: bool
    duration: float = 0.0
    error: str | None = None
    session_id: str | None = None
    agent_id: str | None = None
    action: str | None = None
    resource: str | None = None
    approval_id: str | None = None
    risk_level: str = "safe"
    metadata: dict[str, ToolArgumentValue] = field(
        default_factory=dict
    )
    timestamp: str = ""

    def dump(self) -> dict[str, ToolArgumentValue]:
        return {
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "tool": self.tool,
            "action": self.action,
            "resource": self.resource,
            "approval_id": self.approval_id,
            "risk_level": self.risk_level,
            "success": self.success,
            "duration": self.duration,
            "error": self.error,
            "metadata": dict(self.metadata),
            "timestamp": self.timestamp,
        }
