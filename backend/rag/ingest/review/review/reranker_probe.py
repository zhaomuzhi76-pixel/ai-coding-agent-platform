"""L3 排序模型链路测试器 —— 判定模型是否可被前端选中。"""
from __future__ import annotations

import time
from typing import Any, Protocol

from backend.rag.ingest.review.foundation.reranker_model_spec import (
    RerankerModelSpec,
)
from backend.rag.ingest.review.foundation.reranker_model_status import (
    ProbeOutcome,
)


class RerankerFactory(Protocol):
    def __call__(self, spec: RerankerModelSpec) -> Any: ...


class ProbePolicy:
    def __init__(self, query: str = "链路测试",
                 docs: tuple[str, ...] = (
                     "链路测试文档，用于验证排序模型可用。",
                     "无关内容。",
                 ),
                 min_top_score: float = 0.1,
                 timeout_s: float = 15.0) -> None:
        self.query = query
        self.docs = docs
        self.min_top_score = min_top_score
        self.timeout_s = timeout_s


class RerankerProbe:
    """执行一次轻量打分，判定模型状态。"""

    def __init__(self, factory: RerankerFactory,
                 policy: ProbePolicy | None = None) -> None:
        self._factory = factory
        self._policy = policy or ProbePolicy()

    def run(self, spec: RerankerModelSpec) -> tuple[ProbeOutcome, str, float]:
        started = time.monotonic()
        try:
            instance = self._factory(spec)
        except Exception as e:
            return (ProbeOutcome.NOT_AVAILABLE,
                    f"{type(e).__name__}: {e}", _ms(started))
        if instance is None:
            return ProbeOutcome.NOT_AVAILABLE, "factory returned None", _ms(started)
        try:
            scores = instance.rerank(self._policy.query, list(self._policy.docs))
        except Exception as e:
            return (ProbeOutcome.EXCEPTION,
                    f"{type(e).__name__}: {e}", _ms(started))
        outcome, msg = _judge(scores, self._policy)
        return outcome, msg, _ms(started)


def _judge(scores: Any, policy: ProbePolicy) -> tuple[ProbeOutcome, str]:
    if not scores:
        return ProbeOutcome.EMPTY_RESULT, "empty scores"
    if len(scores) != len(policy.docs):
        return (ProbeOutcome.BAD_SHAPE,
                f"length mismatch: {len(scores)} vs {len(policy.docs)}")
    try:
        top = max(float(s) for s in scores)
    except (TypeError, ValueError):
        return ProbeOutcome.BAD_SHAPE, "non-numeric scores"
    if top < policy.min_top_score:
        return (ProbeOutcome.BAD_SHAPE,
                f"top score {top:.4f} < {policy.min_top_score}")
    return ProbeOutcome.OK, f"top score {top:.4f}"


def _ms(started: float) -> float:
    return round((time.monotonic() - started) * 1000.0, 2)
