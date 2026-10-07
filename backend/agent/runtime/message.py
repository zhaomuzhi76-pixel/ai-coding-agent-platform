"""Agent message: uniform exchange unit."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class AgentMessage:
    role: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_id: Optional[str] = None
    message_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "metadata": dict(self.metadata),
            "parent_id": self.parent_id,
            "message_id": self.message_id,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        return cls(
            role=data["role"],
            content=data["content"],
            metadata=dict(data.get("metadata", {})),
            parent_id=data.get("parent_id"),
            message_id=data.get("message_id", uuid.uuid4().hex[:12]),
            created_at=data.get("created_at", time.time()),
        )

    def dump(self) -> Dict[str, Any]:
        return self.to_dict()
