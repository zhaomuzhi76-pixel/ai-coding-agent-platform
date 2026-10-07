"""Observability report: aggregate tracer + metrics + alerts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.observability.alert import AlertEvent, AlertManager
from backend.observability.tracer import Tracer
from backend.observability.viz import (
    bar_chart, histogram, pct_gauge, sparkline, table,
)


@dataclass
class ObservabilityReport:
    """Snapshot of tracer + frozen metrics + alerts."""

    latency_summary: Dict[str, Any] = field(default_factory=dict)
    per_span: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    durations_ms: List[float] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "latency": dict(self.latency_summary),
            "spans": [dict(s) for s in self.per_span],
            "metrics": dict(self.metrics),
            "alerts": [dict(a) for a in self.alerts],
        }

    def as_text(self, histogram_buckets: int = 8) -> str:
        lines: List[str] = ["=== Observability Report ===", ""]
        # latency summary
        lines.append("-- Latency (ms) --")
        ls = self.latency_summary
        lines.append(
            f"  count={ls.get('count', 0)}  "
            f"p50={ls.get('p50', 0)}  p95={ls.get('p95', 0)}  "
            f"p99={ls.get('p99', 0)}  max={ls.get('max', 0)}"
        )
        lines.append("")
        # per-span table
        if self.per_span:
            lines.append("-- Per-span (ms) --")
            rows = [
                [s["name"], str(s["count"]), str(s["p50"]),
                 str(s["p95"]), str(s["max"])]
                for s in self.per_span
            ]
            lines.append(table(
                ["span", "count", "p50", "p95", "max"], rows,
            ))
            lines.append("")
        # 分布
        if self.durations_ms:
            lines.append("-- Duration distribution --")
            lines.append(histogram(self.durations_ms, buckets=histogram_buckets))
            lines.append("")
        # sparkline
        if self.durations_ms:
            tail = self.durations_ms[-40:]
            lines.append("-- Recent span durations --")
            lines.append(f"  {sparkline(tail)}")
            lines.append("")
        # frozen metrics
        lines.append("-- Frozen metrics (RuntimeMetrics) --")
        m = self.metrics
        if m:
            for k in ("elapsed", "execution_count",
                      "success_count", "failure_count"):
                if k in m:
                    lines.append(f"  {k}: {m[k]}")
            total = int(m.get("execution_count", 0) or 0)
            fails = int(m.get("failure_count", 0) or 0)
            if total > 0:
                rate = (fails / total) * 100.0
                lines.append(f"  failure rate: {pct_gauge(rate)}")
        else:
            lines.append("  (no metrics)")
        lines.append("")
        # alerts
        lines.append("-- Alerts --")
        if not self.alerts:
            lines.append("  (none)")
        else:
            rows = [
                [a["severity"], a["rule"], a["message"]]
                for a in self.alerts
            ]
            lines.append(table(["severity", "rule", "message"], rows))
        return "\n".join(lines)


class ReportBuilder:
    """Collect report data from tracer / frozen metrics / alerts."""

    VERSION = "1.0"

    def build(
        self,
        *,
        tracer: Optional[Tracer] = None,
        metrics_snapshot: Optional[Dict[str, Any]] = None,
        alert_manager: Optional[AlertManager] = None,
    ) -> ObservabilityReport:
        report = ObservabilityReport()

        if tracer is not None:
            report.latency_summary = tracer.summary()
            report.durations_ms = tracer.durations_ms()
            by_name: Dict[str, List[float]] = {}
            for s in tracer.spans():
                if s.ended_at is None:
                    continue
                by_name.setdefault(s.name, []).append(s.duration_ms)
            for name, values in sorted(by_name.items()):
                values.sort()
                n = len(values)
                def pick(p): return values[int(round((p / 100.0) * (n - 1)))]
                report.per_span.append({
                    "name": name,
                    "count": n,
                    "p50": round(pick(50), 3),
                    "p95": round(pick(95), 3),
                    "max": round(values[-1], 3),
                })

        if metrics_snapshot:
            report.metrics = dict(metrics_snapshot)

        if alert_manager is not None:
            report.alerts = [e.to_dict() for e in alert_manager.events()]

        return report

    def render(
        self,
        *,
        tracer: Optional[Tracer] = None,
        metrics_snapshot: Optional[Dict[str, Any]] = None,
        alert_manager: Optional[AlertManager] = None,
    ) -> str:
        return self.build(
            tracer=tracer,
            metrics_snapshot=metrics_snapshot,
            alert_manager=alert_manager,
        ).as_text()

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {"name": type(self).__name__, "version": self.VERSION,
                "ready": self.ready()}


__all__ = ["ObservabilityReport", "ReportBuilder"]
