"""Audit log: append-only access decision history."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class AuditEntry:
    user_id: str
    tenant_id: str
    action: str
    resource: str
    allowed: bool
    reason: str = ""
    entry_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "action": self.action,
            "resource": self.resource,
            "allowed": self.allowed,
            "reason": self.reason,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }

    def dump(self) -> Dict[str, Any]:
        return self.to_dict()


class AuditLog:
    VERSION = "1.0"

    def __init__(self, max_entries: int = 10000) -> None:
        if max_entries <= 0:
            raise ValueError("max_entries must positive")
        self._max = max_entries
        self._entries: List[AuditEntry] = []

    def record(
        self,
        principal_user: str,
        principal_tenant: str,
        action: str,
        resource: str,
        allowed: bool,
        reason: str = "",
        **metadata: Any,
    ) -> AuditEntry:
        entry = AuditEntry(
            user_id=principal_user,
            tenant_id=principal_tenant,
            action=action,
            resource=resource,
            allowed=allowed,
            reason=reason,
            metadata=dict(metadata),
        )
        self._entries.append(entry)
        if len(self._entries) > self._max:
            self._entries = self._entries[-self._max:]
        return entry

    def entries(self) -> List[AuditEntry]:
        return list(self._entries)

    def by_user(self, user_id: str) -> List[AuditEntry]:
        return [e for e in self._entries if e.user_id == user_id]

    def by_tenant(self, tenant_id: str) -> List[AuditEntry]:
        return [e for e in self._entries if e.tenant_id == tenant_id]

    def denials(self) -> List[AuditEntry]:
        return [e for e in self._entries if not e.allowed]

    def count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "count": self.count(),
            "denials": len(self.denials()),
        }


__all__ = ["AuditEntry", "AuditLog"]
