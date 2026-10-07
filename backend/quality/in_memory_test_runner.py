"""内存测试运行器：收集+执行+报告全部在内存中，不落盘、不退出终端。"""
from __future__ import annotations

import io
import traceback
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, List, Sequence

from backend.quality.no_disk_guard import no_disk_writes
from backend.quality.terminal_safety_guard import no_terminal_exit


@dataclass
class TestCase:
    name: str
    fn: Callable[[], None]


@dataclass
class TestOutcome:
    name: str
    passed: bool
    error: str = ""
    stdout: str = ""


@dataclass
class TestReport:
    outcomes: List[TestOutcome] = field(default_factory=list)
    blocked_writes: List[str] = field(default_factory=list)
    blocked_exits: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        clean = not self.blocked_writes and not self.blocked_exits
        return all(o.passed for o in self.outcomes) and clean

    def summary(self) -> str:
        lines = ["=== InMemory Test Report ==="]
        for o in self.outcomes:
            lines.append(f"[{'PASS' if o.passed else 'FAIL'}] {o.name}")
            if o.error:
                lines.append(o.error.rstrip())
        for w in self.blocked_writes:
            lines.append(f"[BLOCKED-WRITE] {w}")
        for e in self.blocked_exits:
            lines.append(f"[BLOCKED-EXIT] {e}")
        lines.append(f"OVERALL: {'PASS' if self.passed else 'FAIL'}")
        return "\n".join(lines)


class InMemoryTestRunner:
    """一次性测试运行器。所有产物只存在于内存。"""

    def __init__(self, cases: Sequence[TestCase]) -> None:
        self._cases = list(cases)

    def run(self) -> TestReport:
        report = TestReport()
        with no_disk_writes() as writes, no_terminal_exit() as exits:
            for case in self._cases:
                report.outcomes.append(self._run_one(case))
            report.blocked_writes.extend(writes)
            report.blocked_exits.extend(exits)
        return report

    @staticmethod
    def _run_one(case: TestCase) -> TestOutcome:
        buf_out = io.StringIO()
        buf_err = io.StringIO()
        try:
            with redirect_stdout(buf_out), redirect_stderr(buf_err):
                case.fn()
            return TestOutcome(name=case.name, passed=True, stdout=buf_out.getvalue())
        except BaseException:  # noqa: BLE001 - 测试期需捕获所有
            return TestOutcome(
                name=case.name,
                passed=False,
                error=traceback.format_exc(),
                stdout=buf_out.getvalue(),
            )
