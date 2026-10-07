"""极简测试框架：不依赖 pytest，不退出终端。"""
from __future__ import annotations

import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class CaseResult:
    name: str
    passed: bool
    duration_ms: float
    error: str = ""
    detail: str = ""


@dataclass
class SuiteReport:
    results: list[CaseResult] = field(default_factory=list)
    started_at: float = 0.0
    finished_at: float = 0.0

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return self.total - self.passed


class Suite:
    def __init__(self, name: str) -> None:
        self.name = name
        self._cases: list[tuple[str, Callable]] = []

    def case(self, fn: Callable) -> Callable:
        self._cases.append((fn.__name__, fn))
        return fn

    def run(self) -> SuiteReport:
        rep = SuiteReport(started_at=time.time())
        for name, fn in self._cases:
            t0 = time.perf_counter()
            try:
                detail = fn()
                rep.results.append(CaseResult(
                    name=name, passed=True,
                    duration_ms=(time.perf_counter() - t0) * 1000,
                    detail=str(detail) if detail else "",
                ))
            except Exception as exc:
                tb = traceback.format_exc()
                rep.results.append(CaseResult(
                    name=name, passed=False,
                    duration_ms=(time.perf_counter() - t0) * 1000,
                    error=f"{type(exc).__name__}: {exc}",
                    detail=tb[-800:],
                ))
        rep.finished_at = time.time()
        return rep


def assert_eq(actual: Any, expected: Any, msg: str = "") -> None:
    if actual != expected:
        raise AssertionError(
            f"{msg} expected={expected!r} actual={actual!r}"
        )


def assert_true(cond: Any, msg: str = "") -> None:
    if not cond:
        raise AssertionError(msg or "condition false")


def assert_in(member: Any, container: Any, msg: str = "") -> None:
    if member not in container:
        raise AssertionError(
            f"{msg} {member!r} not in {container!r}"
        )
