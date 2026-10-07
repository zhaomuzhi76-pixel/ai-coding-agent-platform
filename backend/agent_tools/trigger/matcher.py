"""触发规则匹配器。职责：对 user_text 跑规则，返回首个命中。
不做执行、不做注入、不持状态。registry 用于过滤"未挂载"的工具。
规则按 priority 升序（小优先）。"""
from __future__ import annotations
import re
from typing import Optional, Sequence

from backend.agent_tools.registry import ToolRegistry
from backend.agent_tools.trigger.contracts import TriggerMatch, TriggerRule

class TriggerMatcher:
    def __init__(self, rules: Sequence[TriggerRule]) -> None:
        self._rules = tuple(sorted(rules, key=lambda r: r.priority))
        self._compiled: list = []
        for r in self._rules:
            try:
                self._compiled.append((r, re.compile(r.pattern)))
            except re.error:
                continue

    def rules(self) -> tuple:
        return self._rules

    def match(self, text: str,
              registry: Optional[ToolRegistry] = None) -> Optional[TriggerMatch]:
        if not text or not text.strip():
            return None
        known = set(registry.names()) if registry is not None else None
        for rule, pat in self._compiled:
            if not rule.enabled:
                continue
            if known is not None and rule.tool not in known:
                continue
            m = pat.search(text)
            if not m:
                continue
            args: dict = {}
            for pname, grp in rule.arg_map.items():
                try:
                    v = m.group(int(grp)) if isinstance(grp, int) else m.group(str(grp))
                except (IndexError, KeyError):
                    continue
                if v is None:
                    continue
                s = str(v).strip()
                if s:
                    args[str(pname)] = s
            return TriggerMatch(rule_id=rule.id, tool=rule.tool,
                                arguments=args, matched_text=m.group(0),
                                priority=rule.priority)
        return None

_DEFAULT: Optional[TriggerMatcher] = None

def get_default_matcher() -> TriggerMatcher:
    global _DEFAULT
    if _DEFAULT is None:
        from backend.agent_tools.trigger.rules_builtin import BUILTIN_RULES
        _DEFAULT = TriggerMatcher(BUILTIN_RULES)
    return _DEFAULT

def set_default_matcher(m: Optional[TriggerMatcher]) -> None:
    global _DEFAULT
    _DEFAULT = m

__all__ = ["TriggerMatcher", "get_default_matcher", "set_default_matcher"]
