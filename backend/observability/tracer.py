"""Tracer: collect spans, compute latency percentiles."""
from __future__ import annotations
from backend.core.observability.silent import swallow

from contextlib import contextmanager
from typing import Dict, Iterator, List, Optional

from backend.observability.span import Span

_DEFAULT_MAX_SPANS = 2000


class Tracer:
    """In-memory tracer with a bounded ring of spans."""

    VERSION = "1.0"

    def __init__(self, max_spans: int = _DEFAULT_MAX_SPANS) -> None:
        if max_spans <= 0:
            raise ValueError("max_spans must positive")
        self._max = max_spans
        self._spans: List[Span] = []
        self._stack: List[Span] = []

    # ─── manual control ─────────────────────────────────────
    def start(self, name: str) -> Span:
        parent = self._stack[-1] if self._stack else None
        span = Span(
            name=name,
            parent_id=parent.span_id if parent else None,
        )
        self._stack.append(span)
        self._record(span)
        return span

    def end(
        self, span: Optional[Span] = None,
        *, status: str = "ok", error: str = "",
    ) -> None:
        target = span if span is not None else (
            self._stack[-1] if self._stack else None
        )
        if target is None:
            return
        target.finish(status=status, error=error)
        self._persist(target)
        if self._stack and self._stack[-1] is target:
            self._stack.pop()

    @contextmanager
    def span(
        self, name: str,
    ) -> Iterator[Span]:
        s = self.start(name)
        try:
            yield s
            self.end(s, status="ok")
        except Exception as exc:
            self.end(s, status="error", error=f"{type(exc).__name__}: {exc}")
            raise

    # ─── query ──────────────────────────────────────────────
    def spans(self) -> List[Span]:
        """返回内存 + storage 合并视图（去重）。"""
        try:
            from backend.observability.storage import query_spans
            rows = query_spans(limit=self._max)
            seen = {s.span_id for s in self._spans}
            merged = list(self._spans)
            for r in rows:
                if r["span_id"] in seen:
                    continue
                merged.append(Span(
                    name=r["name"],
                    span_id=r["span_id"],
                    parent_id=r["parent_id"],
                    started_at=r["started_at"],
                    ended_at=r["ended_at"],
                    status=r["status"],
                    error=r["error"],
                    attributes=r.get("attributes") or {},
                ))
            return merged
        except Exception:
            return list(self._spans)

    def by_name(self, name: str) -> List[Span]:
        return [s for s in self.spans() if s.name == name]

    def durations_ms(self, name: Optional[str] = None) -> List[float]:
        spans = self.by_name(name) if name else self.spans()
        return [s.duration_ms for s in spans if s.ended_at is not None]

    def percentile(self, pct: float, name: Optional[str] = None) -> float:
        values = sorted(self.durations_ms(name))
        if not values:
            return 0.0
        pct = max(0.0, min(100.0, pct))
        idx = int(round((pct / 100.0) * (len(values) - 1)))
        return round(values[idx], 3)

    def summary(self, name: Optional[str] = None) -> Dict[str, float]:
        values = sorted(self.durations_ms(name))
        if not values:
            return {"count": 0, "p50": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0}
        n = len(values)
        def pick(p): return values[int(round((p / 100.0) * (n - 1)))]
        return {
            "count": n,
            "p50": round(pick(50), 3),
            "p95": round(pick(95), 3),
            "p99": round(pick(99), 3),
            "max": round(values[-1], 3),
        }

    def errors(self) -> List[Span]:
        return [s for s in self._spans if s.status == "error"]

    def reset(self) -> None:
        self._spans.clear()
        self._stack.clear()
        try:
            from backend.observability.storage import reset_spans
            reset_spans()
        except Exception as e:
            swallow("observability.tracer:126", e)

    # ─── lifecycle ──────────────────────────────────────────
    def _record(self, span: Span) -> None:
        self._spans.append(span)
        if len(self._spans) > self._max:
            self._spans = self._spans[-self._max:]

    def _persist(self, span: Span) -> None:
        """span 结束时落盘（跨进程共享）。"""
        if span.ended_at is None:
            return
        try:
            from backend.observability.storage import insert_span
            insert_span({
                "span_id": span.span_id,
                "name": span.name,
                "parent_id": span.parent_id,
                "status": span.status,
                "duration_ms": span.duration_ms,
                "error": span.error,
                "attributes": span.attributes,
                "started_at": span.started_at,
                "ended_at": span.ended_at,
            })
        except Exception as e:
            swallow("observability.tracer:152", e)

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "count": len(self._spans),
            "errors": len(self.errors()),
        }


__all__ = ["Tracer"]
