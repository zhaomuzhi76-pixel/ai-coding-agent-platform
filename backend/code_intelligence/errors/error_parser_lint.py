from __future__ import annotations

import re
from typing import Any

from backend.code_intelligence.errors.error_parser import (
    ParsedError,
)


# ★ 全部加 re.MULTILINE，支持多行输入
_RUFF = re.compile(
    r"^(?P<file>[^:]+):(?P<line>\d+):(?P<col>\d+): "
    r"(?P<code>[A-Z]\d+)\s+(?P<msg>.+)$",
    re.MULTILINE,
)
_MYPY = re.compile(
    r"^(?P<file>[^:]+):(?P<line>\d+):\s*error:\s*(?P<msg>.+)$",
    re.MULTILINE,
)
_PYTEST_FAIL = re.compile(
    r"^FAILED (?P<file>[^:]+)::(?P<test>[^ ]+)\s*-\s*(?P<msg>.+)$",
    re.MULTILINE,
)
_COMPILE_FILE = re.compile(
    r'^\s*File "(?P<file>.+?)", line (?P<line>\d+)\s*$',
    re.MULTILINE,
)


class LintErrorParser:
    """Ruff / mypy / pytest / SyntaxError 专用解析器。"""

    VERSION = "1.0"
    RESPONSIBILITY = ("lint_error_parsing",)

    def has_ruff(self, text: str) -> bool:
        return bool(_RUFF.search(text))

    def has_mypy(self, text: str) -> bool:
        return bool(_MYPY.search(text))

    def has_pytest(self, text: str) -> bool:
        return bool(_PYTEST_FAIL.search(text))

    def has_syntax(self, text: str) -> bool:
        return (
            "SyntaxError" in text
            or "IndentationError" in text
            or bool(_COMPILE_FILE.search(text))
        )

    def parse_ruff(self, text: str) -> list[ParsedError]:
        out = []
        for m in _RUFF.finditer(text):
            out.append(ParsedError(
                format="ruff",
                file=m.group("file"),
                line=int(m.group("line")),
                function=None,
                error_type=m.group("code"),
                message=m.group("msg"),
                raw=m.group(0),
            ))
        return out

    def parse_mypy(self, text: str) -> list[ParsedError]:
        out = []
        for m in _MYPY.finditer(text):
            out.append(ParsedError(
                format="mypy",
                file=m.group("file"),
                line=int(m.group("line")),
                function=None,
                error_type="MypyError",
                message=m.group("msg"),
                raw=m.group(0),
            ))
        return out

    def parse_pytest(self, text: str) -> list[ParsedError]:
        out = []
        for m in _PYTEST_FAIL.finditer(text):
            out.append(ParsedError(
                format="pytest",
                file=m.group("file"),
                line=None,
                function=m.group("test"),
                error_type="TestFailure",
                message=m.group("msg"),
                raw=m.group(0),
            ))
        return out

    def parse_syntax(self, text: str) -> list[ParsedError]:
        m = _COMPILE_FILE.search(text)
        file_name = m.group("file") if m else None
        line_no = int(m.group("line")) if m else None

        em = re.search(
            r"(SyntaxError|IndentationError):\s*(.+)", text
        )
        if em:
            return [ParsedError(
                format="python_traceback",
                file=file_name,
                line=line_no,
                function=None,
                error_type=em.group(1),
                message=em.group(2),
                raw=text,
            )]
        return []

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
        }


__all__ = ["LintErrorParser"]
