"""规则契约类型定义。

Responsibility:
    - 定义 Rule / RuleResult 不可变数据结构
Not Responsible:
    - 加载 / 校验 / 执行
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Rule:
    id: str
    severity: str
    category: str
    description: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RuleResult:
    rule_id: str
    passed: bool
    findings: tuple[str, ...] = ()
    duration_ms: float = 0.0
    error: str = ""


@dataclass(frozen=True, slots=True)
class Report:
    results: tuple[RuleResult, ...]
    started_at: float
    finished_at: float

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return self.total - self.passed


__all__ = ["Rule", "RuleResult", "Report"]
