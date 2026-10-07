from __future__ import annotations

from pathlib import Path
from typing import Any


class ErrorVerifier:
    """修复后验证：语法 + 可选测试。"""

    VERSION = "1.0"
    RESPONSIBILITY = ("error_fix_verification",)

    def __init__(self, syntax_checker: Any | None = None,
                 test_executor: Any | None = None) -> None:
        if syntax_checker is None:
            from backend.code_intelligence.syntax_checker import SyntaxChecker
            syntax_checker = SyntaxChecker()
        if test_executor is None:
            from backend.code_intelligence.test_executor import TestExecutor
            test_executor = TestExecutor()
        self.syntax_checker = syntax_checker
        self.test_executor = test_executor
        self.verify_count = 0

    def verify(self, *, file: str, workspace: str,
               command: list[str] | None = None) -> dict[str, Any]:
        self.verify_count += 1
        target = Path(workspace) / file if workspace else Path(file)
        syntax = self.syntax_checker.check(str(target))
        if not syntax.get("success", False):
            return {"success": False, "stage": "syntax", "detail": syntax}
        if command:
            test = self.test_executor.execute(command)
            if not test.get("success", False):
                return {"success": False, "stage": "test", "detail": test}
        return {"success": True, "stage": "all", "file": file}

    def ready(self) -> bool:
        return self.syntax_checker is not None and self.test_executor is not None

    def dump(self) -> dict[str, Any]:
        return {"name": type(self).__name__, "version": self.VERSION,
                "responsibility": self.RESPONSIBILITY,
                "ready": self.ready(), "verify_count": self.verify_count}


__all__ = ["ErrorVerifier"]
