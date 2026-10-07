"""Multi-dimension rule reviewer (阿里云: 多维代码审查).

与 ReviewerAgent 的区别：
    ReviewerAgent  -> LLM 语义审查（生成式）
    RuleReviewer   -> 静态规则命中检查（确定性，可审计）
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List


@dataclass
class RuleViolation:
    rule: str
    dimension: str  # style | security | performance | maintainability
    level: str      # info | warning | error
    message: str
    line: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule": self.rule,
            "dimension": self.dimension,
            "level": self.level,
            "message": self.message,
            "line": self.line,
        }


@dataclass
class Rule:
    name: str
    dimension: str
    level: str
    check: Callable[[str, ast.Module], List[str]]


@dataclass
class ReviewReport:
    file: str
    violations: List[RuleViolation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(v.level == "error" for v in self.violations)

    def by_dimension(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for v in self.violations:
            out[v.dimension] = out.get(v.dimension, 0) + 1
        return out

    def dump(self) -> Dict[str, Any]:
        return {
            "file": self.file,
            "ok": self.ok,
            "total": len(self.violations),
            "by_dimension": self.by_dimension(),
            "violations": [v.to_dict() for v in self.violations],
        }


class RuleReviewer:
    VERSION = "1.0"

    def __init__(self) -> None:
        self._rules: List[Rule] = []
        self._register_defaults()

    def add_rule(self, rule: Rule) -> None:
        self._rules.append(rule)

    def review(self, file: str, source: str) -> ReviewReport:
        report = ReviewReport(file=file)
        try:
            tree = ast.parse(source)
        except SyntaxError:
            report.violations.append(RuleViolation(
                rule="syntax", dimension="maintainability",
                level="error", message="source does not parse",
            ))
            return report
        for rule in self._rules:
            try:
                hits = rule.check(source, tree)
            except Exception:
                continue
            for h in hits:
                report.violations.append(RuleViolation(
                    rule=rule.name, dimension=rule.dimension,
                    level=rule.level, message=h,
                ))
        return report

    def _register_defaults(self) -> None:
        self.add_rule(Rule(
            name="no-bare-except",
            dimension="maintainability",
            level="warning",
            check=_check_bare_except,
        ))
        self.add_rule(Rule(
            name="no-eval-exec",
            dimension="security",
            level="error",
            check=_check_eval_exec,
        ))
        self.add_rule(Rule(
            name="no-print",
            dimension="style",
            level="info",
            check=_check_print,
        ))
        self.add_rule(Rule(
            name="max-line-length",
            dimension="style",
            level="info",
            check=_check_line_length,
        ))
        self.add_rule(Rule(
            name="no-mutable-default",
            dimension="maintainability",
            level="warning",
            check=_check_mutable_defaults,
        ))

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "rules": [r.name for r in self._rules],
        }


# ─── default rule implementations ───────────────────────────

def _check_bare_except(source: str, tree: ast.Module) -> List[str]:
    hits: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            hits.append("bare except found")
    return hits


def _check_eval_exec(source: str, tree: ast.Module) -> List[str]:
    hits: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            name = None
            if isinstance(fn, ast.Name):
                name = fn.id
            elif isinstance(fn, ast.Attribute):
                name = fn.attr
            if name in ("eval", "exec", "compile"):
                hits.append(f"use of {name}()")
    return hits


def _check_print(source: str, tree: ast.Module) -> List[str]:
    hits: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id == "print":
            hits.append("print() in source")
    return hits


def _check_line_length(source: str, tree: ast.Module) -> List[str]:
    hits: List[str] = []
    for i, line in enumerate(source.split("\n"), 1):
        if len(line) > 120:
            hits.append(f"line {i}: {len(line)} chars > 120")
    return hits


def _check_mutable_defaults(source: str, tree: ast.Module) -> List[str]:
    hits: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for d in node.args.defaults:
                if isinstance(d, (ast.List, ast.Dict, ast.Set)):
                    hits.append(
                        f"function {node.name} has mutable default"
                    )
    return hits


__all__ = ["RuleViolation", "Rule", "ReviewReport", "RuleReviewer"]
