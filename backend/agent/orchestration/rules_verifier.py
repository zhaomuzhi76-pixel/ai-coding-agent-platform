"""L2 生成后规则校验：把用户规则转成"生成后硬校验"。

工业级（双通道）：
  通道 A · 文本规则（forbid/require）→ 直接在 changes 的 new content 上匹配
  通道 B · 参数规则（rule_param）→ 应用 changes 到 tmpfs 快照，跑 checker

不重复职责：
  · 快照复制 → rules_snapshot
  · 存储 → profile_ops
  · 参数覆盖 → rule_overrides
  · 文件级 checker → project_rules/checks/*
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import re
import shutil
import tempfile
from pathlib import Path

from backend.agent_learning.scope import is_active_for
from backend.agent.orchestration.rules_feedback import (
    RulesFeedback, RulesViolation,
)


class RulesVerifier:
    VERSION = "3.0"

    def __init__(self, workspace: str = "") -> None:
        self._workspace = workspace

    def verify_changes(self, changes: list[dict]) -> RulesFeedback:
        if not self._workspace or not changes:
            return RulesFeedback(ok=True)
        text_v = self._check_text_rules(changes)
        param_v, checked = self._check_param_rules(changes)
        all_v = text_v + param_v
        subs = self._collect_substitutes()
        return RulesFeedback(
            ok=len(all_v) == 0,
            violations=all_v,
            checked_rules=len(text_v) + checked,
            substitutes=subs,
        )

    def _collect_substitutes(self) -> list[str]:
        """从用户 active 规则里提取 require（全局+项目）作为替代提示。"""
        try:
            rules = self._active_text_rules()
        except Exception:
            return []
        subs: list[str] = []
        for p in rules:
            if p.get("key") == "require":
                v = str(p.get("value") or "").strip()
                if v:
                    scope = p.get("scope", "global")
                    subs.append(f"用 '{v}'（{scope}）")
        return subs

    # ── 通道 A：文本规则 ────────────────────────────

    def _active_text_rules(self) -> list[dict]:
        try:
            from backend.agent_learning import profile_ops
            prefs = profile_ops.list_all(
                min_confidence=0, workspace=self._workspace,
            )
        except Exception:
            return []
        return [
            p for p in prefs
            if p.get("kind") == "code_style"
            and is_active_for(p.get("scope", "global"),
                              p.get("workspace", ""), self._workspace)
        ]

    def _check_text_rules(
        self, changes: list[dict],
    ) -> list[RulesViolation]:
        active = self._active_text_rules()
        if not active:
            return []
        out: list[RulesViolation] = []
        for c in changes:
            if not isinstance(c, dict):
                continue
            file = str(c.get("file") or c.get("path") or "?")
            new_content = _extract_new_content(c)
            if not new_content:
                continue
            for p in active:
                key = str(p.get("key") or "")
                val = str(p.get("value") or "").strip()
                if not val:
                    continue
                if key == "forbid":
                    hits = _find_lines(new_content, val)
                    if hits:
                        out.append(RulesViolation(
                            rule_id=f"forbid:{val}", file=file,
                            message=(f"禁止出现 '{val}'，"
                                     f"发现 {len(hits)} 处: "
                                     f"line {hits[0]}"),
                        ))
                elif key == "require":
                    if not _contains_word(new_content, val):
                        out.append(RulesViolation(
                            rule_id=f"require:{val}", file=file,
                            message=f"必须包含 '{val}'（未找到）",
                        ))
        return out

    # ── 通道 B：参数规则（tmpfs 快照） ──────────────

    def _check_param_rules(
        self, changes: list[dict],
    ) -> tuple[list[RulesViolation], int]:
        try:
            from backend.agent_learning.rule_overrides import (
                load_overrides,
            )
            from backend.agent_orchestration.rules_snapshot import (
                apply_snapshot,
            )
            from backend.project_rules.rule_registry import (
                CheckerRegistry,
            )
            from backend.project_rules.rule_types import Rule
        except Exception:
            return [], 0

        ov = load_overrides(workspace=self._workspace)
        if not ov:
            return [], 0
        ws = Path(self._workspace)
        if not ws.is_dir():
            return [], 0

        tmp = Path(tempfile.mkdtemp(prefix="rv-", dir="/dev/shm"))
        try:
            apply_snapshot(ws, tmp, changes)
            reg = CheckerRegistry()
            reg.discover_builtin()
            try:
                reg.register_extended()
            except Exception as e:
                swallow("agent.orchestration.rules_verifier:149", e)
            violations: list[RulesViolation] = []
            checked = 0
            for rule_id, args in ov.items():
                rule = Rule(id=rule_id, severity="error",
                            category="style",
                            description="user-overridden",
                            args=dict(args))
                checker = reg.get(rule_id)
                if checker is None:
                    continue
                checked += 1
                try:
                    r = checker.run(str(tmp), rule)
                except Exception:
                    continue
                if not r.passed:
                    for f in (r.findings or ())[:5]:
                        violations.append(RulesViolation(
                            rule_id=rule_id,
                            file=str(f)[:80],
                            message=str(f)[:200],
                        ))
            return violations, checked
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


# ── 纯函数（模块级，无状态） ──────────────────────

def _extract_new_content(c: dict) -> str:
    k = str(c.get("kind") or "")
    if k == "edit":
        parts = []
        for e in (c.get("edits") or []):
            if isinstance(e, dict):
                parts.append(str(e.get("new") or ""))
        return "\n".join(parts)
    t = c.get("text") or c.get("content") or c.get("new_content")
    return t if isinstance(t, str) else ""


def _contains_word(text: str, word: str) -> bool:
    if not word:
        return True
    if re.match(r"^[\w]+$", word):
        return bool(re.search(r"\b" + re.escape(word) + r"\b", text))
    return word in text


def _find_lines(text: str, word: str) -> list[int]:
    if not word:
        return []
    pat = (r"\b" + re.escape(word) + r"\b"
           if re.match(r"^[\w]+$", word) else re.escape(word))
    return [i for i, line in enumerate(text.split("\n"), 1)
            if re.search(pat, line)]


__all__ = ["RulesVerifier", "RulesFeedback", "RulesViolation"]
