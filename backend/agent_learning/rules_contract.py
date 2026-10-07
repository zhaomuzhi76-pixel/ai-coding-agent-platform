"""L1 契约：项目规则文件（.rules）数据结构。

格式（仿 CLAUDE.md / .cursorrules 但更结构化）：
  # 注释
  forbid=print
  forbid=input
  require=logger
  max_lines=200
  naming=snake_case
  error_handling=try/except
  framework=FastAPI
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


#: 键名 → 默认 kind（未显式给 kind 时用）
KEY_TO_KIND: dict[str, str] = {
    "forbid": "code_style",
    "require": "code_style",
    "max_lines": "code_style",
    "naming": "code_style",
    "error_handling": "workflow",
    "python_version": "workflow",
    "framework": "tech_stack",
    "language": "language",
    "style": "style",
}

#: 已知 key 的预期值类型（用于冲突检测）
VALUE_TYPES: dict[str, str] = {
    "max_lines": "int",
    "python_version": "version",
}


@dataclass(frozen=True)
class Rule:
    kind: str
    key: str
    value: str
    line_no: int = 0
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind, "key": self.key, "value": self.value,
            "line_no": self.line_no, "source": self.source,
        }


@dataclass
class ParseResult:
    rules: list[Rule] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    source_path: str = ""

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "source_path": self.source_path,
            "rule_count": len(self.rules),
            "rules": [r.to_dict() for r in self.rules],
            "errors": list(self.errors),
        }


@dataclass(frozen=True)
class Conflict:
    kind: str
    key: str
    values: tuple[str, ...]
    severity: str = "error"   # error | warn
    reason: str = ""

    def to_line(self) -> str:
        return (
            f"[{self.severity}] {self.kind}.{self.key} 冲突: "
            f"值 {list(self.values)} — {self.reason}"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind, "key": self.key,
            "values": list(self.values),
            "severity": self.severity, "reason": self.reason,
        }


__all__ = ["KEY_TO_KIND", "VALUE_TYPES", "Rule", "ParseResult", "Conflict"]
