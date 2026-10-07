"""Proposal: a code modification proposal (diff-level)."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_APPLIED = "applied"
STATUS_FAILED = "failed"
STATUS_ROLLED_BACK = "rolled_back"


@dataclass
class Proposal:
    """A set of changes awaiting user approval."""

    task: str
    changes: List[Dict[str, Any]]
    plan: str = ""
    attempts: int = 1
    trace: List[Dict[str, Any]] = field(default_factory=list)
    proposal_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    status: str = STATUS_PENDING
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: str = ""
    chunks: List[Dict[str, Any]] = field(default_factory=list)
    analysis_phase: str = "proposed"   # analyzing | proposed | awaiting_approval | applied

    @property
    def file_count(self) -> int:
        return len({
            c.get("file") for c in self.changes if isinstance(c, dict)
        })

    @property
    def pending(self) -> bool:
        return self.status == STATUS_PENDING

    _VALID_PHASES = ("analyzing", "proposed", "awaiting_approval", "applied")

    def set_phase(self, phase: str) -> None:
        if phase not in self._VALID_PHASES:
            raise ValueError(f"invalid phase: {phase}")
        self.analysis_phase = phase
        self.updated_at = time.time()

    def transition(self, new_status: str, error: str = "") -> None:
        valid = {
            STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED,
            STATUS_APPLIED, STATUS_FAILED, STATUS_ROLLED_BACK,
        }
        if new_status not in valid:
            raise ValueError(f"invalid status: {new_status}")
        # 工业级约束：APPLIED 前必须等待批准（防越权 apply）
        if new_status == STATUS_APPLIED and self.analysis_phase != "awaiting_approval":
            raise RuntimeError(
                f"cannot apply before awaiting_approval "
                f"(phase={self.analysis_phase})"
            )
        self.status = new_status
        self.error = error
        self.updated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "task": self.task,
            "plan": self.plan,
            "changes": [dict(c) for c in self.changes if isinstance(c, dict)],
            "attempts": self.attempts,
            "status": self.status,
            "file_count": self.file_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": dict(self.metadata),
            "error": self.error,
            "chunk_count": len(self.chunks),
            "analysis_phase": self.analysis_phase,
        }

    def diff_preview(self, max_chars: int = 4000) -> str:
        """Render a diff preview for frontend display."""
        lines: List[str] = []
        for c in self.changes:
            if not isinstance(c, dict):
                continue
            f = c.get("file", "?")
            kind = c.get("kind", "?")
            text = str(c.get("text", ""))
            lines.append(f"### {f} ({kind})")
            lines.append(text[:1000])
            if len(text) > 1000:
                lines.append(f"...({len(text)-1000} more chars)")
            lines.append("")
        out = "\n".join(lines)
        if len(out) > max_chars:
            out = out[:max_chars] + "\n...(truncated)"
        return out

    def dump(self) -> Dict[str, Any]:
        return self.to_dict()


__all__ = [
    "Proposal",
    "STATUS_PENDING", "STATUS_APPROVED", "STATUS_REJECTED",
    "STATUS_APPLIED", "STATUS_FAILED", "STATUS_ROLLED_BACK",
]
