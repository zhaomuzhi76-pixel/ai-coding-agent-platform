"""L2 确定性 edit 预检。

工业级：能用确定性逻辑判定的，不交给 LLM（避免幻觉）。

检查：
  1. edit 的 `old` 片段是否真在源文件里存在
  2. `old` != `new`（没变化的 edit 无效）
  3. 应用后语法是否合法（py_compile 预检）

不重复职责：
  - LLM 语义审查 → reviewer_agent
  - 编译验证 → local_verifier
  - 本模块只做"确定性结构检查"
"""
from __future__ import annotations

import ast as _ast
import os
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PrecheckIssue:
    file: str
    reason: str
    severity: str = "error"   # error | warn

    def to_line(self) -> str:
        return f"[{self.severity}] {self.file}: {self.reason}"


@dataclass(frozen=True)
class PrecheckResult:
    ok: bool
    issues: tuple[PrecheckIssue, ...] = ()
    can_apply: bool = False
    applied_files: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "can_apply": self.can_apply,
            "issue_count": len(self.issues),
            "issues": [
                {"file": i.file, "reason": i.reason,
                 "severity": i.severity}
                for i in self.issues
            ],
        }


class EditPrecheck:
    VERSION = "1.0"

    def check(
        self,
        *,
        workspace: str,
        changes: list[dict[str, Any]],
    ) -> PrecheckResult:
        if not workspace or not changes:
            return PrecheckResult(ok=False, can_apply=False)

        issues: list[PrecheckIssue] = []
        applied: list[str] = []

        for c in changes:
            if not isinstance(c, dict):
                continue
            file = str(c.get("file") or "").strip()
            kind = str(c.get("kind") or "").strip()
            if not file:
                continue

            full = (
                file if os.path.isabs(file)
                else os.path.join(workspace, file)
            )
            exists = os.path.isfile(full)
            original = ""
            if exists:
                try:
                    with open(full, "r", encoding="utf-8") as fh:
                        original = fh.read()
                except Exception:
                    original = ""

            if kind == "edit":
                new_content = self._apply_edits(
                    original, c.get("edits") or [], file, issues,
                )
                if new_content == original:
                    issues.append(PrecheckIssue(
                        file=file,
                        reason="edit produced no change (old fragment not found or new==old)",
                    ))
                else:
                    self._syntax_check(new_content, file, issues)
                    applied.append(file)
            elif kind == "replace_all":
                text = str(c.get("text") or "")
                if not text.strip():
                    issues.append(PrecheckIssue(
                        file=file, reason="replace_all with empty text"))
                else:
                    self._syntax_check(text, file, issues)
                    applied.append(file)
            elif kind in ("prepend", "append"):
                text = str(c.get("text") or "")
                combined = (
                    text + original if kind == "prepend"
                    else original + text
                )
                self._syntax_check(combined, file, issues)
                applied.append(file)
            elif kind == "create":
                text = str(c.get("text") or "")
                if not text.strip():
                    issues.append(PrecheckIssue(
                        file=file, reason="create with empty text"))
                else:
                    self._syntax_check(text, file, issues)
                    applied.append(file)
            else:
                issues.append(PrecheckIssue(
                    file=file, reason=f"unknown kind: {kind}"))

        # 只看 error 级别
        errors = [i for i in issues if i.severity == "error"]
        ok = (len(errors) == 0) and bool(applied)
        return PrecheckResult(
            ok=ok,
            issues=tuple(issues),
            can_apply=ok,
            applied_files=tuple(applied),
        )

    @staticmethod
    def _apply_edits(
        original: str, edits: list, file: str,
        issues: list[PrecheckIssue],
    ) -> str:
        modified = original
        for e in edits:
            if not isinstance(e, dict):
                continue
            old = e.get("old") or e.get("old_text") or e.get("search") or ""
            new = e.get("new") or e.get("new_text") or e.get("replace") or ""
            if not isinstance(old, str) or not old:
                continue
            if not isinstance(new, str):
                new = ""
            if old not in modified:
                issues.append(PrecheckIssue(
                    file=file,
                    reason=f"old fragment NOT FOUND in file: {old[:60]!r}",
                ))
                continue
            modified = modified.replace(old, new, 1)
        return modified

    @staticmethod
    def _syntax_check(
        content: str, file: str, issues: list[PrecheckIssue],
    ) -> None:
        """只对 .py 文件做 AST 语法检查。"""
        if not file.endswith(".py"):
            return
        try:
            _ast.parse(content)
        except SyntaxError as e:
            issues.append(PrecheckIssue(
                file=file,
                reason=f"syntax error after apply: line {e.lineno}: {e.msg}",
            ))


__all__ = ["EditPrecheck", "PrecheckResult", "PrecheckIssue"]
