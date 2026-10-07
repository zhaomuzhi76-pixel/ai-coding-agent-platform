"""ADR: Architecture Decision Record (Claude Code: 架构演进判断).

与 RepairHistory 的区别：
    RepairHistory -> 每次修复的尝试记录
    ADR           -> 架构级决策（背景、选项、决策、后果）
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_STATUSES = ("proposed", "accepted", "rejected", "superseded")


@dataclass
class ADR:
    title: str
    context: str
    decision: str
    consequences: str = ""
    status: str = "proposed"
    alternatives: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    adr_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: float = field(default_factory=time.time)
    supersedes: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("adr.title required")
        if self.status not in _STATUSES:
            raise ValueError(f"status must {_STATUSES}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "adr_id": self.adr_id,
            "title": self.title,
            "status": self.status,
            "context": self.context,
            "decision": self.decision,
            "consequences": self.consequences,
            "alternatives": list(self.alternatives),
            "tags": list(self.tags),
            "created_at": self.created_at,
            "supersedes": self.supersedes,
        }

    def dump(self) -> Dict[str, Any]:
        return self.to_dict()


class ADRLog:
    VERSION = "1.0"

    def __init__(self) -> None:
        self._log: List[ADR] = []

    def add(self, adr: ADR) -> ADR:
        self._log.append(adr)
        return adr

    def propose(
        self, title: str, context: str, decision: str,
        consequences: str = "", **extra: Any,
    ) -> ADR:
        return self.add(ADR(
            title=title, context=context, decision=decision,
            consequences=consequences, **extra,
        ))

    def accept(self, adr_id: str) -> None:
        self._transition(adr_id, "accepted")

    def reject(self, adr_id: str) -> None:
        self._transition(adr_id, "rejected")

    def supersede(self, old_id: str, new_id: str) -> None:
        for a in self._log:
            if a.adr_id == old_id:
                a.status = "superseded"
        for a in self._log:
            if a.adr_id == new_id:
                a.supersedes = old_id

    def get(self, adr_id: str) -> Optional[ADR]:
        for a in self._log:
            if a.adr_id == adr_id:
                return a
        return None

    def list(self, status: Optional[str] = None) -> List[ADR]:
        if status is None:
            return list(self._log)
        return [a for a in self._log if a.status == status]

    def by_tag(self, tag: str) -> List[ADR]:
        return [a for a in self._log if tag in a.tags]

    def count(self) -> int:
        return len(self._log)

    def _transition(self, adr_id: str, status: str) -> None:
        a = self.get(adr_id)
        if a is None:
            raise KeyError(adr_id)
        a.status = status

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "count": self.count(),
            "by_status": {
                s: len(self.list(s)) for s in _STATUSES
            },
        }


__all__ = ["ADR", "ADRLog"]
