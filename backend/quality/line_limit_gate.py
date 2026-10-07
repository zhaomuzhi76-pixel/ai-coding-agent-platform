"""单文件行数门禁：>230 失败，>200 警告。"""
from __future__ import annotations

import os
from typing import Iterator, List

from backend.quality.gate_contract import GateContext, GateResult, GateViolation

DEFAULT_HARD = 230
DEFAULT_SOFT = 200


class LineLimitGate:
    name = "line_limit"
    layer = "quality"

    def __init__(self, hard: int = DEFAULT_HARD, soft: int = DEFAULT_SOFT) -> None:
        self._hard = hard
        self._soft = soft

    def run(self, ctx: GateContext) -> GateResult:
        violations: List[GateViolation] = []
        metrics = {"hard": self._hard, "soft": self._soft, "scanned": 0}
        for path in self._iter_py(ctx.root):
            metrics["scanned"] += 1
            lines = self._count_lines(path)
            rel = os.path.relpath(path, ctx.root)
            if lines > self._hard:
                violations.append(GateViolation(
                    code="LINE_HARD_LIMIT",
                    message=f"{rel} has {lines} lines (> {self._hard})",
                    location=rel,
                    severity="error",
                ))
            elif lines > self._soft:
                violations.append(GateViolation(
                    code="LINE_SOFT_LIMIT",
                    message=f"{rel} has {lines} lines (> {self._soft})",
                    location=rel,
                    severity="warning",
                ))
        passed = not any(v.severity == "error" for v in violations)
        return GateResult(name=self.name, passed=passed,
                          violations=violations, metrics=metrics)

    @staticmethod
    def _iter_py(root: str) -> Iterator[str]:
        for base, _dirs, files in os.walk(root):
            for name in files:
                if name.endswith(".py"):
                    yield os.path.join(base, name)

    @staticmethod
    def _count_lines(path: str) -> int:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return sum(1 for _ in fh)
