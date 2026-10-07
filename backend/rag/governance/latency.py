"""延迟预算追踪。零依赖、可嵌套、可测量。"""
from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Dict, Iterator, List, Optional

from .contracts import LatencyReport

# 默认预算（从 backend/config/rag_governance 读；env 可覆盖）
from backend.config.rag_governance import get_rag_config as _get_rag_cfg
DEFAULT_BUDGET_MS = _get_rag_cfg().default_budget_ms


class LatencyBudget:
    """记录各阶段耗时；超预算置 over_budget=True。"""

    def __init__(self, budget_ms: int = DEFAULT_BUDGET_MS) -> None:
        self.budget_ms = budget_ms
        self._stages: Dict[str, float] = {}
        self._order: List[str] = []
        self._start: Optional[float] = None

    def start(self) -> None:
        self._start = time.perf_counter()

    @contextmanager
    def stage(self, name: str) -> Iterator[None]:
        """用法：with budget.stage("retrieve"): ..."""
        t0 = time.perf_counter()
        try:
            yield
        finally:
            dt = (time.perf_counter() - t0) * 1000.0
            self._stages[name] = self._stages.get(name, 0.0) + dt
            if name not in self._order:
                self._order.append(name)

    def mark(self, name: str, ms: float) -> None:
        self._stages[name] = self._stages.get(name, 0.0) + float(ms)
        if name not in self._order:
            self._order.append(name)

    def report(self) -> LatencyReport:
        total = sum(self._stages.values())
        return LatencyReport(
            stages=dict(self._stages),
            total_ms=total,
            budget_ms=self.budget_ms,
            over_budget=total > self.budget_ms,
        )


@contextmanager
def stopwatch() -> Iterator[callable]:
    """用法：
        with stopwatch() as t:
            ...
        elapsed_ms = t()
    """
    t0 = time.perf_counter()
    box: List[float] = [0.0]

    def elapsed() -> float:
        box[0] = (time.perf_counter() - t0) * 1000.0
        return box[0]

    yield elapsed


def summarize(report: LatencyReport) -> str:
    parts = [f"{k}={v:.0f}ms" for k, v in report.stages.items()]
    head = f"total={report.total_ms:.0f}ms/{report.budget_ms}ms"
    tail = " ⚠ OVER" if report.over_budget else " ✓"
    return f"[latency] {head}  " + " ".join(parts) + tail


__all__ = ["DEFAULT_BUDGET_MS", "LatencyBudget", "stopwatch", "summarize"]
