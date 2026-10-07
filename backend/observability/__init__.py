"""Observability layer.

复用冻结层：
    runtime.observability.RuntimeMetrics  -> 计时 + 计数
    runtime.observability.MetricsStore    -> 5 固定 key 的 KV
新增本层只做：span/tracer、alert、report、viz。
"""
from backend.observability.span import Span
from backend.observability.tracer import Tracer
from backend.observability.alert import (
    AlertRule, AlertEvent, AlertManager,
    latency_p95_over, error_rate_over, failure_count_over,
)
from backend.observability.report import (
    ObservabilityReport, ReportBuilder,
)
from backend.observability.viz import (
    sparkline, bar_chart, table, histogram, pct_gauge,
)

__all__ = [
    "Span", "Tracer",
    "AlertRule", "AlertEvent", "AlertManager",
    "latency_p95_over", "error_rate_over", "failure_count_over",
    "ObservabilityReport", "ReportBuilder",
    "sparkline", "bar_chart", "table", "histogram", "pct_gauge",
]
