"""L1 契约：规则作用域（global / project / session）。"""
from __future__ import annotations

import re
from enum import Enum


class RuleScope(str, Enum):
    GLOBAL = "global"
    PROJECT = "project"
    SESSION = "session"


_PATTERNS: tuple[tuple[str, re.Pattern], ...] = (
    (RuleScope.SESSION.value, re.compile(
        r"(?:这次|本次|暂时|先|临时|当前会话|这个会话)")),
    (RuleScope.PROJECT.value, re.compile(
        r"(?:这个项目|本项目|本仓库|当前项目|项目里|此项目|"
        r"这份代码|这代码库|repo(?:sitory)?)")),
    (RuleScope.GLOBAL.value, re.compile(
        r"(?:以后|永久|所有项目|我总是|永远|一贯|每次|一直|跨项目)")),
)


def detect_scope(
    message: str, *, workspace: str = "",
    default: RuleScope = RuleScope.GLOBAL,
) -> RuleScope:
    if not message:
        return default
    for value, regex in _PATTERNS:
        if regex.search(message):
            try:
                return RuleScope(value)
            except ValueError:
                continue
    if workspace and workspace.strip():
        return RuleScope.PROJECT
    return default


def scope_label(scope: str) -> str:
    return {"global": "全局", "project": "项目",
            "session": "会话"}.get(scope, scope)


def is_active_for(
    scope: str, rule_workspace: str, current_workspace: str,
) -> bool:
    if scope == RuleScope.GLOBAL.value:
        return True
    return (rule_workspace or "") == (current_workspace or "")


__all__ = ["RuleScope", "detect_scope", "scope_label", "is_active_for"]
