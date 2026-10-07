"""Track tokens and cost per model."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class CallRecord:
    model: str
    input_tokens: int
    output_tokens: int
    cost: float


@dataclass
class ModelUsage:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0


class CostTracker:
    """In-memory cost tracker."""

    def __init__(self) -> None:
        self._per_model: Dict[str, ModelUsage] = {}
        self._history: List[CallRecord] = []

    def record(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_input_per_1k: float = 0.0,
        cost_output_per_1k: float = 0.0,
    ) -> CallRecord:
        cost = (
            input_tokens / 1000.0 * cost_input_per_1k
            + output_tokens / 1000.0 * cost_output_per_1k
        )
        rec = CallRecord(
            model=model,
            input_tokens=int(input_tokens),
            output_tokens=int(output_tokens),
            cost=cost,
        )
        self._history.append(rec)
        usage = self._per_model.setdefault(model, ModelUsage())
        usage.calls += 1
        usage.input_tokens += rec.input_tokens
        usage.output_tokens += rec.output_tokens
        usage.cost += cost
        return rec

    def per_model(self) -> Dict[str, ModelUsage]:
        return dict(self._per_model)

    def total_cost(self) -> float:
        return sum(u.cost for u in self._per_model.values())

    def total_calls(self) -> int:
        return sum(u.calls for u in self._per_model.values())

    def history(self) -> List[CallRecord]:
        return list(self._history)

    def reset(self) -> None:
        self._per_model.clear()
        self._history.clear()

    def ready(self) -> bool:
        return True

    def dump(self) -> dict:
        return {
            "ready": self.ready(),
            "total_calls": self.total_calls(),
            "total_cost": round(self.total_cost(), 6),
            "models": {
                m: {"calls": u.calls, "cost": round(u.cost, 6)}
                for m, u in self._per_model.items()
            },
        }
