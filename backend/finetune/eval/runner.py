"""Eval runner: run samples through a predictor and compute metrics."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

from backend.finetune.eval.metrics import (
    contains_match, exact_match, token_f1,
)


@dataclass
class EvalItem:
    user: str
    gold: str
    pred: str
    exact: bool
    contains: bool
    f1: float


@dataclass
class EvalReport:
    items: List[EvalItem] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.items)

    @property
    def exact_rate(self) -> float:
        if not self.items:
            return 0.0
        return sum(1 for i in self.items if i.exact) / len(self.items)

    @property
    def contains_rate(self) -> float:
        if not self.items:
            return 0.0
        return sum(1 for i in self.items if i.contains) / len(self.items)

    @property
    def mean_f1(self) -> float:
        if not self.items:
            return 0.0
        return sum(i.f1 for i in self.items) / len(self.items)

    def summary(self) -> Dict[str, Any]:
        return {
            "count": self.count,
            "exact_rate": round(self.exact_rate, 4),
            "contains_rate": round(self.contains_rate, 4),
            "mean_f1": round(self.mean_f1, 4),
        }


class EvalRunner:
    def __init__(self, predict: Callable[[str], str]) -> None:
        self._predict = predict

    def run(self, samples: List[Dict[str, str]]) -> EvalReport:
        report = EvalReport()
        for s in samples:
            user = str(s.get("user", ""))
            gold = str(s.get("assistant", s.get("gold", "")))
            try:
                pred = self._predict(user)
            except Exception as exc:
                pred = f"<error:{type(exc).__name__}>"
            report.items.append(EvalItem(
                user=user, gold=gold, pred=pred,
                exact=exact_match(pred, gold),
                contains=contains_match(pred, gold),
                f1=token_f1(pred, gold),
            ))
        return report
