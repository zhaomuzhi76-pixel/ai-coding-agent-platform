"""规则 schema 校验。

工业级：category 不再硬编码白名单 ——
  - 默认接受任意非空、形如 [a-z_]+ 的 category
  - 可通过环境变量 PROJECT_RULES_CATEGORIES 收紧（逗号分隔）
Not Responsible:
  - 加载 YAML（loader）
  - 执行检查（checks/*）
"""
from __future__ import annotations

import os
import re
from typing import Any

from .rule_types import Rule


class RuleSchemaError(ValueError):
    """规则 schema 不合法。"""


#: category 的语法约束（非值白名单）
_CATEGORY_RE = re.compile(r"^[a-z][a-z0-9_]{0,31}$")

#: 用户可选收紧（环境变量），未设则不限
_ENV_CATEGORIES = os.environ.get("PROJECT_RULES_CATEGORIES", "").strip()
ALLOWED_CATEGORIES: tuple[str, ...] = (
    tuple(c.strip() for c in _ENV_CATEGORIES.split(",") if c.strip())
    if _ENV_CATEGORIES else ()
)


def parse_rule(item: dict[str, Any]) -> Rule:
    if not isinstance(item, dict):
        raise RuleSchemaError(f"rule must dict, got {type(item).__name__}")
    rid = str(item.get("id") or "").strip()
    if not rid:
        raise RuleSchemaError("rule.id required")
    severity = str(item.get("severity") or "error").strip()
    if severity not in ("error", "warn", "info"):
        raise RuleSchemaError(
            f"invalid severity: {severity!r} "
            "(expected error|warn|info)"
        )
    category = str(item.get("category") or "process").strip()
    if not _CATEGORY_RE.match(category):
        raise RuleSchemaError(
            f"invalid category syntax: {category!r} "
            "(expected lowercase [a-z_]+)"
        )
    if ALLOWED_CATEGORIES and category not in ALLOWED_CATEGORIES:
        raise RuleSchemaError(
            f"category {category!r} not in PROJECT_RULES_CATEGORIES "
            f"{list(ALLOWED_CATEGORIES)}"
        )
    description = str(item.get("description") or "").strip()
    args = item.get("args") or {}
    if not isinstance(args, dict):
        raise RuleSchemaError("rule.args must dict")
    return Rule(id=rid, severity=severity, category=category,
                description=description, args=dict(args))


def parse_all(items: list[Any]) -> list[Rule]:
    if not isinstance(items, list):
        raise RuleSchemaError("rules must be a list")
    return [parse_rule(x) for x in items]


__all__ = [
    "RuleSchemaError", "ALLOWED_CATEGORIES",
    "parse_rule", "parse_all",
]
