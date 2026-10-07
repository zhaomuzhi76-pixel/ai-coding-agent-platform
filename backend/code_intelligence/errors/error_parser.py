from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ParsedError:
    """结构化错误。"""
    format: str
    file: str | None
    line: int | None
    function: str | None
    error_type: str
    message: str
    stack: list[dict[str, Any]] = field(default_factory=list)
    raw: str = ""

    def ready(self) -> bool:
        return bool(self.error_type and self.message)

    def dump(self) -> dict[str, Any]:
        return {
            "format": self.format,
            "file": self.file,
            "line": self.line,
            "function": self.function,
            "error_type": self.error_type,
            "message": self.message,
            "stack": list(self.stack),
        }


# ★ 加 MULTILINE 支持多行
_TB_FRAME = re.compile(
    r'^\s+File "(?P<file>.+?)", line (?P<line>\d+), '
    r'in (?P<func>.+)$',
    re.MULTILINE,
)
_TB_ERROR = re.compile(
    r"^(?P<etype>[A-Za-z_][\w.]*(?:Error|Exception|Warning))"
    r":\s*(?P<msg>.*)$",
    re.MULTILINE,
)


class ErrorParser:
    """
    把任意格式错误输出解析成 ParsedError 列表。

    支持：python_traceback / ruff / mypy / pytest / syntax
    """

    VERSION = "2.0"
    RESPONSIBILITY = ("structured_error_parsing",)

    def __init__(self) -> None:
        # 延迟 import 避免循环
        from backend.code_intelligence.errors.error_parser_lint import (
            LintErrorParser,
        )
        self._lint = LintErrorParser()

    def parse(self, raw: str) -> list[ParsedError]:
        if not isinstance(raw, str) or not raw.strip():
            return []

        text = raw.strip()

        if self._has_traceback(text):
            out = self._parse_traceback(text)
            if out:
                return out

        if self._lint.has_ruff(text):
            out = self._lint.parse_ruff(text)
            if out:
                return out

        if self._lint.has_mypy(text):
            out = self._lint.parse_mypy(text)
            if out:
                return out

        if self._lint.has_pytest(text):
            out = self._lint.parse_pytest(text)
            if out:
                return out

        if self._lint.has_syntax(text):
            out = self._lint.parse_syntax(text)
            if out:
                return out

        return [ParsedError(
            format="unknown",
            file=None, line=None, function=None,
            error_type="UnknownError",
            message=text[:500],
            raw=text,
        )]

    @staticmethod
    def _has_traceback(text: str) -> bool:
        return "Traceback (most recent call last):" in text

    def _parse_traceback(self, text: str) -> list[ParsedError]:
        stack: list[dict[str, Any]] = []
        for m in _TB_FRAME.finditer(text):
            stack.append({
                "file": m.group("file"),
                "line": int(m.group("line")),
                "function": m.group("func"),
            })

        err_m = None
        for m in _TB_ERROR.finditer(text):
            err_m = m  # 取最后一个（最内层错误）
        if not err_m:
            return []

        etype = err_m.group("etype").split(".")[-1]
        msg = err_m.group("msg")
        leaf = stack[-1] if stack else {}

        return [ParsedError(
            format="python_traceback",
            file=leaf.get("file"),
            line=leaf.get("line"),
            function=leaf.get("function"),
            error_type=etype,
            message=f"{etype}: {msg}",
            stack=stack,
            raw=text,
        )]

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
        }


__all__ = ["ErrorParser", "ParsedError"]
