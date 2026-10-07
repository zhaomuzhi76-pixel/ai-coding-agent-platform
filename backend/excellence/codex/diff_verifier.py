"""Diff-level verifier (Codex: 可验证的修改结果).

与 VerificationRunner 的区别：
    VerificationRunner -> 执行语法/测试命令，看结果
    DiffVerifier       -> 只看 before/after 文本，检查结构约束
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class DiffIssue:
    level: str       # error | warning
    code: str
    message: str
    file: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"level": self.level, "code": self.code,
                "message": self.message, "file": self.file}


@dataclass
class DiffReport:
    file: str
    before_lines: int
    after_lines: int
    issues: List[DiffIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.level == "error" for i in self.issues)

    @property
    def delta(self) -> int:
        return self.after_lines - self.before_lines

    def dump(self) -> Dict[str, Any]:
        return {
            "file": self.file,
            "before_lines": self.before_lines,
            "after_lines": self.after_lines,
            "delta": self.delta,
            "ok": self.ok,
            "issues": [i.to_dict() for i in self.issues],
        }


class DiffVerifier:
    """Structural checks on before/after text without running tests."""

    VERSION = "1.0"

    def __init__(self, max_growth_lines: int = 500) -> None:
        self._max_growth = max_growth_lines

    def verify(
        self, file: str, before: str, after: str,
    ) -> DiffReport:
        report = DiffReport(
            file=file,
            before_lines=before.count("\n") + 1,
            after_lines=after.count("\n") + 1,
        )
        if report.delta > self._max_growth:
            report.issues.append(DiffIssue(
                level="error", code="GROWTH_TOO_LARGE",
                message=f"file grew by {report.delta} lines "
                        f"(limit {self._max_growth})",
                file=file,
            ))
        if after and not after.endswith("\n"):
            report.issues.append(DiffIssue(
                level="warning", code="NO_TRAILING_NEWLINE",
                message="file does not end with newline", file=file,
            ))
        if file.endswith(".py"):
            self._check_python(file, after, report)
        return report

    @staticmethod
    def _check_python(
        file: str, after: str, report: DiffReport,
    ) -> None:
        try:
            ast.parse(after)
        except SyntaxError as exc:
            report.issues.append(DiffIssue(
                level="error", code="SYNTAX_ERROR",
                message=f"{exc.msg} (line {exc.lineno})", file=file,
            ))

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "max_growth_lines": self._max_growth,
        }


__all__ = ["DiffIssue", "DiffReport", "DiffVerifier"]
