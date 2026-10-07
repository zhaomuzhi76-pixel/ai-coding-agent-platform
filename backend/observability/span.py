"""Span: a single traced operation."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Span:
    """One traced operation: start / end / duration / metadata."""

    name: str
    span_id: str = field(
        default_factory=lambda: uuid.uuid4().hex[:12]
    )
    parent_id: Optional[str] = None
    started_at: float = field(default_factory=time.time)
    ended_at: Optional[float] = None
    status: str = "running"  # running | ok | error
    error: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        if self.ended_at is None:
            return 0.0
        return (self.ended_at - self.started_at) * 1000.0

    def finish(self, *, status: str = "ok", error: str = "") -> None:
        if self.ended_at is not None:
            return
        self.ended_at = time.time()
        self.status = status
        self.error = error

    def set(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "status": self.status,
            "duration_ms": round(self.duration_ms, 3),
            "error": self.error,
            "attributes": dict(self.attributes),
        }

    def dump(self) -> Dict[str, Any]:
        return self.to_dict()


__all__ = ["Span"]
