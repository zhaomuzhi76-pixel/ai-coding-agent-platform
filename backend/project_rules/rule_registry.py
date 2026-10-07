"""Checker 注册表：每个规则对应一个插件。

Responsibility:
    - 注册 / 查找 Checker 插件
    - 自动发现 checks/ 目录下的插件
Not Responsible:
    - 执行检查（那是 runner）
"""
from __future__ import annotations

import importlib
import pkgutil
from typing import Protocol

from .rule_types import Rule, RuleResult


class Checker(Protocol):
    rule_id: str
    def run(self, root_path: str, rule: Rule) -> RuleResult: ...


class CheckerRegistry:
    VERSION = "1.0"

    def __init__(self) -> None:
        self._checkers: dict[str, Checker] = {}

    def register(self, checker: Checker) -> None:
        rid = getattr(checker, "rule_id", "")
        if not rid:
            raise ValueError("checker must define rule_id")
        if rid in self._checkers:
            raise ValueError(f"duplicate checker: {rid}")
        self._checkers[rid] = checker

    def get(self, rule_id: str) -> Checker | None:
        return self._checkers.get(rule_id)

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._checkers.keys()))

    def register_extended(self) -> int:
        """显式注册扩展 Checker（不走 _check 后缀自动发现）。"""
        try:
            from backend.project_rules.checks.extended_checks import (
                register_all,
            )
        except Exception:
            return 0
        return register_all(self)

    def discover_builtin(self) -> int:
        """自动发现 checks 包下所有 *_check 模块里的 Checker 实例。"""
        pkg = importlib.import_module(
            "backend.project_rules.checks"
        )
        n = 0
        for _, mod_name, _ in pkgutil.iter_modules(pkg.__path__):
            if not mod_name.endswith("_check"):
                continue
            mod = importlib.import_module(
                f"backend.project_rules.checks.{mod_name}"
            )
            checker = getattr(mod, "CHECKER", None)
            if checker is None:
                continue
            self.register(checker)
            n += 1
        return n


__all__ = ["Checker", "CheckerRegistry"]
