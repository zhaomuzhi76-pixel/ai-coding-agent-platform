"""L2 本地验证适配器。

职责：把 verification_runner + error_parser 组合成
orchestrator 可直接调用的 verify(changes, workspace) -> VerificationFeedback。

不重复职责：
  - 语法检查/测试执行 → verification_runner
  - 错误解析 → error_parser
  - 本模块只做"编排 + 结果归一化"
"""
from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from backend.agent.orchestration.verification_feedback import (
    VerificationFeedback,
    VerifyIssue,
)


class LocalVerifier:
    VERSION = "1.0"

    def __init__(
        self,
        verifier: Any = None,
        parser: Any = None,
    ) -> None:
        self._verifier = verifier
        self._parser = parser

    def _get_verifier(self) -> Any:
        if self._verifier is not None:
            return self._verifier
        try:
            from backend.code_intelligence.verification_runner import (
                VerificationRunner,
            )
        except Exception:
            return None
        # VerificationRunner 需要 syntax_checker + test_executor
        try:
            from backend.code_intelligence.syntax_checker import (
                SyntaxChecker,
            )
        except Exception:
            SyntaxChecker = None
        try:
            from backend.code_intelligence.test_executor import (
                TestExecutor,
            )
        except Exception:
            TestExecutor = None
        if SyntaxChecker is None or TestExecutor is None:
            return None
        try:
            self._verifier = VerificationRunner(
                syntax_checker=SyntaxChecker(),
                test_executor=TestExecutor(),
            )
            return self._verifier
        except Exception:
            return None

    def _get_parser(self) -> Any:
        if self._parser is not None:
            return self._parser
        try:
            from backend.code_intelligence.errors.error_parser import (
                ErrorParser,
            )
            self._parser = ErrorParser()
            return self._parser
        except Exception:
            return None

    def verify_changes(
        self,
        *,
        workspace: str,
        files: list[str],
        run_tests: bool = False,
        timeout: int = 30,
    ) -> VerificationFeedback:
        """对一组文件做验证。"""
        verifier = self._get_verifier()
        if verifier is None:
            return VerificationFeedback(
                ok=True, verify_available=False,
                raw="(verification_runner not available)",
            )
        if not files:
            return VerificationFeedback(ok=True, raw="(no files to verify)")

        raw_outputs: list[str] = []
        issues: list[VerifyIssue] = []
        ok = True

        for f in files:
            try:
                result = verifier.verify(
                    f, root=workspace, timeout=timeout,
                )
            except Exception as e:
                raw_outputs.append(f"{f}: verify error: {e}")
                continue
            r_ok, r_text = self._normalize(result)
            raw_outputs.append(f"=== {f} ===\n{r_text}")
            if not r_ok:
                ok = False
                issues.extend(self._parse_errors(f, r_text))

        return VerificationFeedback(
            ok=ok,
            issues=tuple(issues),
            raw="\n".join(raw_outputs),
            verify_available=True,
        )

    @staticmethod
    def _normalize(result: Any) -> tuple[bool, str]:
        """兼容各种可能的 verify 返回结构。"""
        if isinstance(result, dict):
            ok = bool(
                result.get("ok")
                or result.get("success")
                or result.get("passed")
            )
            text_parts = []
            for k in ("stdout", "stderr", "output", "message",
                      "error", "errors", "detail"):
                v = result.get(k)
                if v:
                    text_parts.append(str(v))
            if not text_parts:
                text_parts.append(str(result))
            return ok, "\n".join(text_parts)
        if isinstance(result, bool):
            return result, ""
        if isinstance(result, str):
            return True, result
        return True, str(result)

    def _parse_errors(self, file: str, text: str) -> list[VerifyIssue]:
        parser = self._get_parser()
        if parser is None or not text.strip():
            return []
        try:
            parsed = parser.parse(text)
        except Exception:
            return []
        out: list[VerifyIssue] = []
        for e in parsed or []:
            out.append(VerifyIssue(
                file=str(getattr(e, "file", "") or file),
                line=int(getattr(e, "line", 0) or 0),
                message=str(getattr(e, "message", "") or "")[:300],
                severity=str(getattr(e, "severity", "") or "error"),
                source=str(getattr(e, "format", "") or "syntax"),
            ))
        return out


__all__ = ["LocalVerifier"]
