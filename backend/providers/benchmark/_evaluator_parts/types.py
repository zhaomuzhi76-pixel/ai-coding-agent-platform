"""评分器类型定义（独立，避免循环依赖）"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Judgment:
    passed: bool
    score: float
    note: str = ""
    evidence: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be in [0, 1]")
