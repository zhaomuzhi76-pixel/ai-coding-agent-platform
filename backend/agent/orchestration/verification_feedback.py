"""L1 契约：验证反馈数据结构。

工业级：把 verification_runner 的输出 + error_parser 的结果
统一成结构化反馈，供 orchestrator 循环使用。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class VerifyIssue:
    """单条验证问题。"""
    file: str
    line: int = 0
    message: str = ""
    severity: str = "error"
    source: str = "syntax"   # syntax | ruff | mypy | pytest | traceback

    def to_line(self) -> str:
        loc = f"{self.file}:{self.line}" if self.line else self.file
        return f"[{self.source}] {loc}: {self.message}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "file": self.file, "line": self.line,
            "message": self.message, "severity": self.severity,
            "source": self.source,
        }


@dataclass(frozen=True)
class VerificationFeedback:
    """验证结果汇总。"""
    ok: bool
    issues: tuple[VerifyIssue, ...] = ()
    raw: str = ""
    verify_available: bool = True
    meta: dict[str, Any] = field(default_factory=dict)

    def to_feedback_text(self, max_issues: int = 8) -> str:
        """转成给 LLM 的重试反馈文本。"""
        if self.ok:
            return ""
        lines = ["[Local verification FAILED]"]
        if not self.verify_available:
            lines.append("(verifier unavailable, treating as pass)")
            return ""
        for i, issue in enumerate(self.issues[:max_issues], 1):
            lines.append(f"  {i}. {issue.to_line()}")
        if len(self.issues) > max_issues:
            lines.append(
                f"  ... ({len(self.issues) - max_issues} more issues)"
            )
        if not self.issues:
            lines.append("  (no structured issues, see raw output below)")
            lines.append(self.raw[:500])
        lines.append("")
        lines.append(
            "Please FIX the above issues and reply with the corrected JSON."
        )
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "verify_available": self.verify_available,
            "issue_count": len(self.issues),
            "issues": [i.to_dict() for i in self.issues],
            "raw_preview": self.raw[:500],
        }


__all__ = ["VerifyIssue", "VerificationFeedback"]
