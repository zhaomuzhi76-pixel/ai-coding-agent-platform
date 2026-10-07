"""EventBridge: feed platform execution into observability tracer."""
from __future__ import annotations

from typing import Any, Dict, Optional

from backend.observability.registry import get_tracer
from backend.observability.tracer import Tracer


class EventBridge:
    """Translate platform phase boundaries into tracer spans."""

    VERSION = "1.1"

    def __init__(self, tracer: Optional[Tracer] = None) -> None:
        self._tracer = tracer or get_tracer()

    @property
    def tracer(self) -> Tracer:
        return self._tracer

    def phase(self, name: str):
        return self._tracer.span(name)

    def record(self, name: str, duration_ms: float, ok: bool,
               error: str = "") -> None:
        s = self._tracer.start(name)
        s.set("manual", True)
        s.set("duration_ms_reported", duration_ms)
        self._tracer.end(
            s,
            status="ok" if ok else "error",
            error=error,
        )

    def summary(self, phase: Optional[str] = None) -> Dict[str, Any]:
        return dict(self._tracer.summary(phase))

    def errors(self) -> list:
        return [s.to_dict() for s in self._tracer.errors()]

    def ready(self) -> bool:
        return self._tracer.ready()

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "spans": len(self._tracer.spans()),
        }


__all__ = ["EventBridge"]
