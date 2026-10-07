"""ObservabilityBinding: HTTP adapter over global tracer/alerts."""
from __future__ import annotations

from typing import Any, Dict

from backend.observability.registry import (
    get_alert_manager,
    get_tracer,
)
from backend.observability.report import ReportBuilder


class ObservabilityBinding:
    VERSION = "1.0"
    PREFIX = "/api/observability"

    def __init__(self) -> None:
        self._report = ReportBuilder()

    def summary(self) -> Dict[str, Any]:
        t = get_tracer()
        return {
            "overall": t.summary(),
            "spans": len(t.spans()),
            "errors": len(t.errors()),
            "alerts": len(get_alert_manager().events()),
        }

    def spans(self, limit: int = 200) -> Dict[str, Any]:
        t = get_tracer()
        all_spans = t.spans()
        tail = all_spans[-limit:] if limit > 0 else all_spans
        return {
            "total": len(all_spans),
            "spans": [s.to_dict() for s in tail],
        }

    def by_name(self, name: str) -> Dict[str, Any]:
        t = get_tracer()
        items = t.by_name(name)
        return {
            "name": name,
            "count": len(items),
            "summary": t.summary(name),
            "spans": [s.to_dict() for s in items[-100:]],
        }

    def errors(self) -> Dict[str, Any]:
        return {"errors": [s.to_dict() for s in get_tracer().errors()]}

    def alerts(self) -> Dict[str, Any]:
        return {
            "events": [e.to_dict() for e in get_alert_manager().events()]
        }

    def report(self, buckets: int = 8) -> Dict[str, Any]:
        t = get_tracer()
        a = get_alert_manager()
        rep = self._report.build(tracer=t, alert_manager=a)
        return {
            "data": rep.as_dict(),
            "text": rep.as_text(histogram_buckets=buckets),
        }

    def reset(self) -> Dict[str, Any]:
        get_tracer().reset()
        get_alert_manager().clear()
        return {"reset": True}

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "prefix": self.PREFIX,
            "ready": self.ready(),
        }


__all__ = ["ObservabilityBinding"]
