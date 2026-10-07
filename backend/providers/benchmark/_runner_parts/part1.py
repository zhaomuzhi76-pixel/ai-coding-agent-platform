"""Part 1 of runner.py."""
from __future__ import annotations

import asyncio

import time

from dataclasses import dataclass, field

from typing import Any, AsyncIterator, Awaitable, Callable

from ..cases import BenchmarkCase, list_cases

from ..evaluator import BenchmarkCaseResult, evaluate_case

ChatFn = Callable[[list[dict], dict], Awaitable[str]]

StreamFn = Callable[[list[dict], dict], AsyncIterator[str]]

CostFn = Callable[[str, int, int], float]

DEFAULT_CASE_TIMEOUT = 60.0

DEFAULT_TOTAL_TIMEOUT = 600.0

@dataclass
class BenchmarkResult:
    provider: str
    model: str
    started_at: float
    finished_at: float
    cases: tuple[BenchmarkCaseResult, ...]
    score: float                   # 0 ~ 100 加权总分
    rating: str                    # A+ / A / B+ / B / C / D
    by_category: dict[str, float] = field(default_factory=dict)
    error: str = ""

    @property
    def elapsed_sec(self) -> float:
        return round(self.finished_at - self.started_at, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "elapsed_sec": self.elapsed_sec,
            "score": round(self.score, 2),
            "rating": self.rating,
            "by_category": {k: round(v, 2) for k, v in self.by_category.items()},
            "cases": [c.to_dict() for c in self.cases],
            "error": self.error,
        }

def score_to_rating(score: float) -> str:
    """0~100 → 字母评级。"""
    if score >= 95: return "A+"
    if score >= 85: return "A"
    if score >= 75: return "B+"
    if score >= 65: return "B"
    if score >= 55: return "C"
    return "D"

def aggregate_score(results: tuple[BenchmarkCaseResult, ...]) -> float:
    """加权平均 → 0~100。"""
    if not results:
        return 0.0
    total_w = 0.0
    total_ws = 0.0
    for r in results:
        w = 1.0  # 目前等权；将来可从 case.weight 取
        total_w += w
        total_ws += r.score * w
    if total_w == 0:
        return 0.0
    return (total_ws / total_w) * 100.0

def aggregate_by_category(
    results: tuple[BenchmarkCaseResult, ...],
) -> dict[str, float]:
    by_cat: dict[str, list[float]] = {}
    for r in results:
        by_cat.setdefault(r.category, []).append(r.score)
    return {k: (sum(v) / len(v)) * 100.0 for k, v in by_cat.items()}
