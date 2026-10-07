"""模型响应判定器（10 个用例的评分逻辑）。

职责：
    - judge 函数：输入响应文本 → 输出 Judgment
    - evaluate_case：组合多次执行为 BenchmarkCaseResult

命名：
    BenchmarkCaseResult · 避免与 backend/tests/industrial/framework.py CaseResult 冲突
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable

from ._evaluator_parts import (
    judge_noop,
    judge_json_follow,
    judge_tool_call,
    judge_chinese,
    judge_long_context,
    judge_reasoning,
)  # noqa: F401
from .cases import BenchmarkCase
from ._evaluator_parts.judges import _JUDGES
from ._evaluator_parts.types import Judgment  # noqa: F401
from ._evaluator_parts._util import extract_json as _extract_json





@dataclass
class BenchmarkCaseResult:
    case_id: str
    name: str
    category: str
    passed: bool
    score: float
    latency_ms: float = 0.0
    first_token_ms: float = 0.0
    cost: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    note: str = ""
    evidence: str = ""
    attempts: int = 1
    successes: int = 1
    error: str = ""
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "name": self.name,
            "category": self.category,
            "passed": self.passed,
            "score": round(self.score, 4),
            "latency_ms": round(self.latency_ms, 2),
            "first_token_ms": round(self.first_token_ms, 2),
            "cost": round(self.cost, 6),
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "note": self.note,
            "evidence": self.evidence[:200],
            "attempts": self.attempts,
            "successes": self.successes,
            "error": self.error,
            "extra": dict(self.extra),
        }


def _ev(text: str) -> str:
    return (text or "").strip()[:200]





def get_judge(name: str) -> Callable[[str], Judgment]:
    n = (name or "").strip()
    if n not in _JUDGES:
        raise KeyError("unknown judge: " + n)
    return _JUDGES[n]


def evaluate_case(
    case: BenchmarkCase,
    responses: list[str],
    latency_ms: float = 0.0,
    first_token_ms: float = 0.0,
    cost: float = 0.0,
    input_tokens: int = 0,
    output_tokens: int = 0,
    error: str = "",
) -> BenchmarkCaseResult:
    if not responses:
        return BenchmarkCaseResult(
            case_id=case.case_id, name=case.name, category=case.category,
            passed=False, score=0.0,
            latency_ms=latency_ms, first_token_ms=first_token_ms,
            cost=cost, input_tokens=input_tokens, output_tokens=output_tokens,
            error=error or "no responses",
        )
    judge = get_judge(case.judge)
    judgments = [judge(r) for r in responses]
    score = sum(j.score for j in judgments) / len(judgments)
    passed = score >= 0.7 and not error
    successes = sum(1 for j in judgments if j.passed)
    notes = " | ".join(j.note for j in judgments if j.note)
    return BenchmarkCaseResult(
        case_id=case.case_id, name=case.name, category=case.category,
        passed=passed, score=score,
        latency_ms=latency_ms, first_token_ms=first_token_ms,
        cost=cost, input_tokens=input_tokens, output_tokens=output_tokens,
        note=notes, evidence=judgments[-1].evidence,
        attempts=len(responses), successes=successes, error=error,
    )


__all__ = [
    "Judgment",
    "BenchmarkCaseResult",
    "get_judge",
    "evaluate_case",
    "judge_noop",
    "judge_json_follow",
    "judge_tool_call",
    "judge_chinese",
    "judge_long_context",
    "judge_reasoning",
]

